"""
╔══════════════════════════════════════════════════════════════════╗
║  NetVista 3D — IPv4 Fragmentation Engine                        ║
║  Core simulation logic for IPv4 packet fragmentation            ║
║  Student ID: 25CS052 | Advanced Learner Group                   ║
║  Course: ITUC201 – Fundamentals of Computer Networks 2026-27    ║
╚══════════════════════════════════════════════════════════════════╝

This module implements the complete IPv4 fragmentation algorithm with:
- 20-byte IPv4 header (no options)
- 8-byte offset granularity (Fragment Offset field)
- Multi-hop fragmentation across routers with different MTUs
- Don't Fragment (DF) bit handling
- Full validation suite (payload coverage, offset continuity, MF flags)
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
import math
import json
import csv
import io


# ─── Constants ────────────────────────────────────────────────────
IPV4_HEADER_SIZE = 20        # bytes (no options)
MIN_MTU = 68                 # RFC 791 minimum MTU
MAX_MTU = 65535              # Maximum IPv4 packet size
OFFSET_UNIT = 8              # Fragment offset granularity in bytes
MAX_PAYLOAD = 65535 - IPV4_HEADER_SIZE  # Maximum payload size


@dataclass
class Fragment:
    """Represents a single IPv4 fragment."""
    fragment_id: int              # Sequential fragment number (1-based)
    hop: int                      # Router hop number where fragmentation occurred
    mtu_at_hop: int               # MTU of the link at this hop
    payload_size: int             # Payload bytes in this fragment
    header_size: int              # IPv4 header size (always 20 bytes)
    total_size: int               # header_size + payload_size
    byte_offset: int              # Byte offset from start of original payload
    offset_in_units: int          # byte_offset / 8 (value in Fragment Offset field)
    more_fragments: bool          # MF flag (True = more fragments follow)
    payload_range: Tuple[int, int]  # (start_byte, end_byte) inclusive range
    parent_fragment_id: Optional[int] = None  # ID of parent fragment if re-fragmented

    @property
    def mf_flag(self) -> int:
        return 1 if self.more_fragments else 0

    def to_dict(self) -> dict:
        return {
            "Fragment #": self.fragment_id,
            "Hop": self.hop,
            "MTU (bytes)": self.mtu_at_hop,
            "Payload (bytes)": self.payload_size,
            "Header (bytes)": self.header_size,
            "Total Size (bytes)": self.total_size,
            "Byte Offset": self.byte_offset,
            "Offset (÷8)": self.offset_in_units,
            "MF Flag": self.mf_flag,
            "Payload Range": f"{self.payload_range[0]}–{self.payload_range[1]}",
        }


@dataclass
class FragmentationResult:
    """Complete result of a fragmentation simulation."""
    original_payload: int
    mtu_path: List[int]
    fragments: List[Fragment]
    hop_details: List[Dict]     # Per-hop fragmentation summary
    df_flag: bool
    error: Optional[str] = None
    
    @property
    def total_fragments(self) -> int:
        return len(self.fragments)
    
    @property
    def total_header_overhead(self) -> int:
        return self.total_fragments * IPV4_HEADER_SIZE
    
    @property
    def overhead_percentage(self) -> float:
        if self.original_payload == 0:
            return 0.0
        return (self.total_header_overhead / self.original_payload) * 100
    
    @property
    def total_bytes_transmitted(self) -> int:
        return sum(f.total_size for f in self.fragments)


@dataclass
class ValidationResult:
    """Result of fragment validation checks."""
    is_valid: bool
    checks: List[Dict]  # Each dict has: name, passed, detail


@dataclass
class ReassemblyEvent:
    """Represents a single step in the destination reassembly sequence."""
    step: int
    fragment_id: int
    offset: int
    payload_size: int
    mf_flag: int
    payload_range: Tuple[int, int]
    holes_after: List[Tuple[int, int]]
    buffered_bytes_after: int
    buffer_percent: float
    description: str


@dataclass
class ReassemblySimulationResult:
    """Complete output of destination host reassembly simulation."""
    success: bool
    original_payload: int
    reassembled_payload: int
    total_fragments_sent: int
    fragments_received: List[Fragment]
    dropped_fragments: List[Fragment]
    arrival_order_name: str
    arrival_sequence: List[int]
    final_holes: List[Tuple[int, int]]
    events: List[ReassemblyEvent]
    icmp_generated: bool
    icmp_type: int = 11
    icmp_code: int = 1
    icmp_name: str = "ICMP Time Exceeded (Fragment Reassembly Time Exceeded)"
    icmp_description: str = ""
    timeout_seconds: float = 30.0



class FragmentationEngine:
    """
    IPv4 Fragmentation Simulator Engine.
    
    Implements multi-hop fragmentation following RFC 791 rules:
    1. Each fragment payload must be a multiple of 8 bytes (except the last)
    2. Fragment Offset is measured in 8-byte units
    3. The MF flag is set on all fragments except the last
    4. If DF flag is set, the packet is dropped when MTU < packet size
    """

    @staticmethod
    def fragment_packet(
        payload_size: int,
        mtu_path: List[int],
        df_flag: bool = False,
    ) -> FragmentationResult:
        """
        Simulate IPv4 fragmentation across a path of routers with varying MTUs.
        
        Args:
            payload_size: Original payload size in bytes (excluding IPv4 header)
            mtu_path: List of MTU values at each hop [hop1_mtu, hop2_mtu, ...]
            df_flag: If True, simulate Don't Fragment behavior
            
        Returns:
            FragmentationResult with all fragments and metadata
        """
        # ── Input validation ──
        if payload_size <= 0:
            return FragmentationResult(
                original_payload=payload_size, mtu_path=mtu_path,
                fragments=[], hop_details=[], df_flag=df_flag,
                error="Payload size must be positive."
            )
        
        if payload_size > MAX_PAYLOAD:
            return FragmentationResult(
                original_payload=payload_size, mtu_path=mtu_path,
                fragments=[], hop_details=[], df_flag=df_flag,
                error=f"Payload exceeds maximum ({MAX_PAYLOAD} bytes)."
            )
        
        if not mtu_path:
            return FragmentationResult(
                original_payload=payload_size, mtu_path=mtu_path,
                fragments=[], hop_details=[], df_flag=df_flag,
                error="At least one MTU value is required."
            )
        
        for i, mtu in enumerate(mtu_path):
            if mtu < MIN_MTU:
                return FragmentationResult(
                    original_payload=payload_size, mtu_path=mtu_path,
                    fragments=[], hop_details=[], df_flag=df_flag,
                    error=f"MTU at hop {i+1} ({mtu}) is below RFC 791 minimum ({MIN_MTU} bytes)."
                )
        
        # ── DF flag check ──
        original_total = payload_size + IPV4_HEADER_SIZE
        if df_flag:
            for i, mtu in enumerate(mtu_path):
                if original_total > mtu:
                    return FragmentationResult(
                        original_payload=payload_size, mtu_path=mtu_path,
                        fragments=[], hop_details=[], df_flag=df_flag,
                        error=(
                            f"🚫 DF (Don't Fragment) flag is set! "
                            f"Packet size ({original_total} bytes) exceeds MTU at hop {i+1} "
                            f"({mtu} bytes). Packet DROPPED. "
                            f"ICMP 'Fragmentation Needed' (Type 3, Code 4) sent to source."
                        )
                    )
            # No fragmentation needed — packet fits through all hops
            frag = Fragment(
                fragment_id=1, hop=0, mtu_at_hop=mtu_path[0],
                payload_size=payload_size, header_size=IPV4_HEADER_SIZE,
                total_size=original_total, byte_offset=0, offset_in_units=0,
                more_fragments=False, payload_range=(0, payload_size - 1),
            )
            return FragmentationResult(
                original_payload=payload_size, mtu_path=mtu_path,
                fragments=[frag], hop_details=[], df_flag=df_flag,
            )

        # ── Multi-hop fragmentation ──
        # Start with the original packet as a single "fragment"
        current_fragments: List[Dict] = [{
            "payload_size": payload_size,
            "byte_offset": 0,
            "more_fragments": False,
            "parent_id": None,
        }]
        
        hop_details = []
        global_frag_id = 0
        
        for hop_idx, mtu in enumerate(mtu_path):
            hop_num = hop_idx + 1
            max_payload_per_frag = mtu - IPV4_HEADER_SIZE
            # Round down to nearest multiple of 8
            max_payload_aligned = (max_payload_per_frag // OFFSET_UNIT) * OFFSET_UNIT
            
            new_fragments = []
            fragments_created_this_hop = 0
            fragments_input = len(current_fragments)
            
            for frag in current_fragments:
                frag_total = frag["payload_size"] + IPV4_HEADER_SIZE
                
                if frag_total <= mtu:
                    # Fragment fits, no further fragmentation needed
                    new_fragments.append(frag)
                    continue
                
                # Need to fragment this packet
                remaining = frag["payload_size"]
                current_offset = frag["byte_offset"]
                original_mf = frag["more_fragments"]
                parent_id = frag.get("parent_id")
                
                sub_fragments = []
                while remaining > 0:
                    if remaining + IPV4_HEADER_SIZE <= mtu:
                        # Last fragment — take all remaining bytes
                        chunk = remaining
                        mf = original_mf  # Inherit MF from parent
                    else:
                        # Not the last fragment — must be aligned to 8 bytes
                        chunk = max_payload_aligned
                        mf = True
                    
                    sub_fragments.append({
                        "payload_size": chunk,
                        "byte_offset": current_offset,
                        "more_fragments": mf,
                        "parent_id": parent_id,
                        "hop_created": hop_num,
                        "mtu_at_hop": mtu,
                    })
                    
                    current_offset += chunk
                    remaining -= chunk
                    fragments_created_this_hop += 1
                
                new_fragments.extend(sub_fragments)
            
            hop_details.append({
                "hop": hop_num,
                "mtu": mtu,
                "fragments_in": fragments_input,
                "fragments_out": len(new_fragments),
                "fragmentation_occurred": len(new_fragments) > fragments_input,
            })
            
            current_fragments = new_fragments
        
        # ── Build final Fragment objects ──
        final_fragments = []
        for idx, frag in enumerate(current_fragments):
            global_frag_id = idx + 1
            hop_created = frag.get("hop_created", 0)
            mtu_at = frag.get("mtu_at_hop", mtu_path[0] if mtu_path else 0)
            
            end_byte = frag["byte_offset"] + frag["payload_size"] - 1
            
            final_fragments.append(Fragment(
                fragment_id=global_frag_id,
                hop=hop_created,
                mtu_at_hop=mtu_at,
                payload_size=frag["payload_size"],
                header_size=IPV4_HEADER_SIZE,
                total_size=frag["payload_size"] + IPV4_HEADER_SIZE,
                byte_offset=frag["byte_offset"],
                offset_in_units=frag["byte_offset"] // OFFSET_UNIT,
                more_fragments=frag["more_fragments"],
                payload_range=(frag["byte_offset"], end_byte),
                parent_fragment_id=frag.get("parent_id"),
            ))
        
        return FragmentationResult(
            original_payload=payload_size,
            mtu_path=mtu_path,
            fragments=final_fragments,
            hop_details=hop_details,
            df_flag=df_flag,
        )

    @staticmethod
    def validate_fragments(result: FragmentationResult) -> ValidationResult:
        """
        Run comprehensive validation checks on fragmentation results.
        
        Checks:
        1. Complete payload coverage (no gaps, no overlaps)
        2. Correct byte offsets (ascending, aligned to 8)
        3. MF flag correctness (all set except last)
        4. Fragment sizes within MTU limits
        5. Total reassembled payload matches original
        """
        checks = []
        all_passed = True
        
        if result.error or not result.fragments:
            checks.append({
                "name": "Fragment existence",
                "passed": False,
                "detail": result.error or "No fragments generated.",
            })
            return ValidationResult(is_valid=False, checks=checks)
        
        fragments = sorted(result.fragments, key=lambda f: f.byte_offset)
        
        # ── Check 1: Payload coverage ──
        total_payload_bytes = sum(f.payload_size for f in fragments)
        coverage_ok = total_payload_bytes == result.original_payload
        checks.append({
            "name": "✅ Payload Coverage" if coverage_ok else "❌ Payload Coverage",
            "passed": coverage_ok,
            "detail": (
                f"Sum of fragment payloads ({total_payload_bytes} B) "
                f"{'matches' if coverage_ok else 'does NOT match'} "
                f"original payload ({result.original_payload} B)."
            ),
        })
        if not coverage_ok:
            all_passed = False
        
        # ── Check 2: No gaps or overlaps ──
        gap_overlap_ok = True
        gap_details = []
        for i in range(len(fragments) - 1):
            expected_next_offset = fragments[i].byte_offset + fragments[i].payload_size
            actual_next_offset = fragments[i + 1].byte_offset
            if actual_next_offset != expected_next_offset:
                gap_overlap_ok = False
                if actual_next_offset > expected_next_offset:
                    gap_details.append(
                        f"Gap of {actual_next_offset - expected_next_offset} B "
                        f"between fragment {fragments[i].fragment_id} and {fragments[i+1].fragment_id}"
                    )
                else:
                    gap_details.append(
                        f"Overlap of {expected_next_offset - actual_next_offset} B "
                        f"between fragment {fragments[i].fragment_id} and {fragments[i+1].fragment_id}"
                    )
        
        checks.append({
            "name": "✅ No Gaps/Overlaps" if gap_overlap_ok else "❌ Gaps/Overlaps Detected",
            "passed": gap_overlap_ok,
            "detail": "All fragments are contiguous." if gap_overlap_ok else "; ".join(gap_details),
        })
        if not gap_overlap_ok:
            all_passed = False
        
        # ── Check 3: Offset alignment (must be multiples of 8) ──
        alignment_ok = all(f.byte_offset % OFFSET_UNIT == 0 for f in fragments)
        misaligned = [f.fragment_id for f in fragments if f.byte_offset % OFFSET_UNIT != 0]
        checks.append({
            "name": "✅ Offset Alignment (8-byte)" if alignment_ok else "❌ Offset Alignment",
            "passed": alignment_ok,
            "detail": (
                "All fragment offsets are multiples of 8 bytes."
                if alignment_ok else
                f"Fragments {misaligned} have offsets not aligned to 8 bytes."
            ),
        })
        if not alignment_ok:
            all_passed = False
        
        # ── Check 4: MF flag correctness ──
        mf_ok = True
        mf_details = []
        for i, f in enumerate(fragments):
            if i < len(fragments) - 1:
                if not f.more_fragments:
                    mf_ok = False
                    mf_details.append(f"Fragment {f.fragment_id}: MF should be 1 (not last)")
            else:
                if f.more_fragments:
                    mf_ok = False
                    mf_details.append(f"Fragment {f.fragment_id}: MF should be 0 (last fragment)")
        
        checks.append({
            "name": "✅ MF Flag Correctness" if mf_ok else "❌ MF Flag Error",
            "passed": mf_ok,
            "detail": (
                "MF=1 on all fragments except the last (MF=0). Correct!"
                if mf_ok else "; ".join(mf_details)
            ),
        })
        if not mf_ok:
            all_passed = False
        
        # ── Check 5: Fragment sizes within MTU ──
        size_ok = True
        size_details = []
        # We check each fragment against the MTU where it was created
        for f in fragments:
            if f.mtu_at_hop > 0 and f.total_size > f.mtu_at_hop:
                size_ok = False
                size_details.append(
                    f"Fragment {f.fragment_id}: size {f.total_size} B > MTU {f.mtu_at_hop} B"
                )
        
        checks.append({
            "name": "✅ Size ≤ MTU" if size_ok else "❌ Fragment Exceeds MTU",
            "passed": size_ok,
            "detail": (
                "All fragments fit within their respective link MTU."
                if size_ok else "; ".join(size_details)
            ),
        })
        if not size_ok:
            all_passed = False
        
        # ── Check 6: First fragment starts at offset 0 ──
        first_ok = fragments[0].byte_offset == 0
        checks.append({
            "name": "✅ First Offset = 0" if first_ok else "❌ First Offset ≠ 0",
            "passed": first_ok,
            "detail": (
                f"First fragment starts at byte offset 0."
                if first_ok else
                f"First fragment starts at offset {fragments[0].byte_offset} (should be 0)."
            ),
        })
        if not first_ok:
            all_passed = False
        
        return ValidationResult(is_valid=all_passed, checks=checks)

    @staticmethod
    def run_experiment(
        payload_size: int = 4000,
        mtu_values: Optional[List[int]] = None,
    ) -> List[Dict]:
        """
        Run a controlled experiment: fixed payload, varying single MTU.
        
        Returns a list of measurement dicts for each MTU value.
        """
        if mtu_values is None:
            mtu_values = list(range(100, 1520, 20))
        
        measurements = []
        for mtu in mtu_values:
            if mtu < MIN_MTU:
                continue
            result = FragmentationEngine.fragment_packet(payload_size, [mtu])
            if result.error:
                continue
            
            measurements.append({
                "MTU (bytes)": mtu,
                "Fragment Count": result.total_fragments,
                "Total Header Overhead (bytes)": result.total_header_overhead,
                "Overhead %": round(result.overhead_percentage, 2),
                "Total Bytes Transmitted": result.total_bytes_transmitted,
                "Efficiency %": round(
                    (payload_size / result.total_bytes_transmitted) * 100, 2
                ) if result.total_bytes_transmitted > 0 else 0,
            })
        
        return measurements

    @staticmethod
    def run_multi_hop_experiment(
        payload_size: int = 4000,
        mtu_paths: Optional[List[List[int]]] = None,
    ) -> List[Dict]:
        """
        Run experiment with different multi-hop MTU paths.
        """
        if mtu_paths is None:
            mtu_paths = [
                [1500],
                [1500, 620],
                [1500, 620, 400],
                [1500, 1000, 620, 400],
                [1500, 800, 600, 400, 200],
                [1500, 1200, 1000, 800, 600],
                [500, 1500],            # Increasing MTU (no re-fragmentation)
                [400, 800, 1500],       # Increasing MTU path
                [1500, 200, 1500],      # Bottleneck in middle
                [1500, 576],            # Common internet minimum
            ]
        
        measurements = []
        for path in mtu_paths:
            result = FragmentationEngine.fragment_packet(payload_size, path)
            if result.error:
                continue
            
            measurements.append({
                "MTU Path": " → ".join(map(str, path)),
                "Min MTU": min(path),
                "Fragment Count": result.total_fragments,
                "Total Header Overhead (bytes)": result.total_header_overhead,
                "Overhead %": round(result.overhead_percentage, 2),
                "Total Bytes Transmitted": result.total_bytes_transmitted,
            })
        
        return measurements

    @staticmethod
    def simulate_reassembly(
        result: FragmentationResult,
        arrival_mode: str = "in_order",
        dropped_fragment_ids: Optional[List[int]] = None,
        timeout_seconds: float = 30.0,
    ) -> ReassemblySimulationResult:
        """
        Simulate RFC 791 Datagram Reassembly at the Destination Host.
        
        Args:
            result: FragmentationResult containing generated fragments.
            arrival_mode: 'in_order', 'reverse_order', or 'scrambled'.
            dropped_fragment_ids: List of fragment IDs dropped/lost in transit.
            timeout_seconds: Reassembly timer timeout value in seconds.
            
        Returns:
            ReassemblySimulationResult detailing hole tracking, events, and ICMP status.
        """
        if not result.fragments or result.error:
            return ReassemblySimulationResult(
                success=False,
                original_payload=result.original_payload,
                reassembled_payload=0,
                total_fragments_sent=0,
                fragments_received=[],
                dropped_fragments=[],
                arrival_order_name=arrival_mode,
                arrival_sequence=[],
                final_holes=[],
                events=[],
                icmp_generated=False,
                icmp_description="No fragments available for reassembly."
            )
        
        dropped_ids = set(dropped_fragment_ids or [])
        total_payload = result.original_payload
        
        # Determine arrival sequence
        all_frags = list(result.fragments)
        if arrival_mode == "in_order":
            ordered_frags = sorted(all_frags, key=lambda f: f.byte_offset)
            order_name = "In-Order Arrival (F1 → Fn)"
        elif arrival_mode == "reverse_order":
            ordered_frags = sorted(all_frags, key=lambda f: f.byte_offset, reverse=True)
            order_name = "Reverse-Order Arrival (Fn → F1)"
        elif arrival_mode == "scrambled":
            # Deterministic multi-path scrambled arrival pattern
            n = len(all_frags)
            indices = []
            evens = [i for i in range(n) if i % 2 == 0]
            odds = [i for i in range(n) if i % 2 != 0]
            # Interleave odd and even indices
            for e, o in zip(evens, odds):
                indices.extend([o, e])
            if len(evens) > len(odds):
                indices.append(evens[-1])
            ordered_frags = [all_frags[i] for i in indices]
            order_name = "Multi-Path Scrambled / Out-of-Order Arrival"
        else:
            ordered_frags = list(all_frags)
            order_name = "Standard Arrival"
        
        arrival_sequence = [f.fragment_id for f in ordered_frags]
        received_frags = [f for f in ordered_frags if f.fragment_id not in dropped_ids]
        dropped_frags = [f for f in all_frags if f.fragment_id in dropped_ids]
        
        # RFC 791 Hole Descriptor Algorithm
        # Initial hole spans the entire payload range [0, total_payload - 1]
        holes: List[List[int]] = [[0, total_payload - 1]]
        events: List[ReassemblyEvent] = []
        buffered_bytes = 0
        step_counter = 1
        
        for frag in ordered_frags:
            if frag.fragment_id in dropped_ids:
                # Fragment was lost in transit!
                events.append(ReassemblyEvent(
                    step=step_counter,
                    fragment_id=frag.fragment_id,
                    offset=frag.byte_offset,
                    payload_size=frag.payload_size,
                    mf_flag=frag.mf_flag,
                    payload_range=frag.payload_range,
                    holes_after=[(h[0], h[1]) for h in holes],
                    buffered_bytes_after=buffered_bytes,
                    buffer_percent=round((buffered_bytes / total_payload) * 100, 1),
                    description=f"⚠️ Fragment #{frag.fragment_id} [Bytes {frag.payload_range[0]}–{frag.payload_range[1]}] was LOST in transit (Simulated Packet Loss)."
                ))
                step_counter += 1
                continue
            
            f_start = frag.byte_offset
            f_end = frag.byte_offset + frag.payload_size - 1
            
            new_holes: List[List[int]] = []
            for h in holes:
                h_start, h_end = h[0], h[1]
                if f_start > h_end or f_end < h_start:
                    # No overlap with this hole
                    new_holes.append([h_start, h_end])
                else:
                    # Fragment covers part or all of this hole
                    if f_start > h_start:
                        new_holes.append([h_start, f_start - 1])
                    if f_end < h_end:
                        new_holes.append([f_end + 1, h_end])
            
            holes = new_holes
            buffered_bytes += frag.payload_size
            buf_pct = min(100.0, round((buffered_bytes / total_payload) * 100, 1))
            
            holes_summary = ", ".join([f"[{h[0]}–{h[1]}]" for h in holes]) if holes else "None (Fully Closed)"
            mf_str = "MF=1 (More fragments follow)" if frag.more_fragments else "MF=0 (Final fragment of datagram)"
            desc = (
                f"📥 Fragment #{frag.fragment_id} arrived: Bytes {frag.payload_range[0]}–{frag.payload_range[1]} "
                f"({frag.payload_size} B, Offset={frag.offset_in_units}, {mf_str}). "
                f"Remaining holes: {holes_summary}."
            )
            
            events.append(ReassemblyEvent(
                step=step_counter,
                fragment_id=frag.fragment_id,
                offset=frag.byte_offset,
                payload_size=frag.payload_size,
                mf_flag=frag.mf_flag,
                payload_range=frag.payload_range,
                holes_after=[(h[0], h[1]) for h in holes],
                buffered_bytes_after=buffered_bytes,
                buffer_percent=buf_pct,
                description=desc
            ))
            step_counter += 1
        
        final_holes = [(h[0], h[1]) for h in holes]
        is_success = len(final_holes) == 0 and buffered_bytes == total_payload
        
        if is_success:
            icmp_gen = False
            icmp_desc = ""
        else:
            icmp_gen = True
            missing_ranges_str = ", ".join([f"Bytes {h[0]}–{h[1]} ({h[1]-h[0]+1} B)" for h in final_holes])
            lost_ids_str = ", ".join([f"#{fid}" for fid in sorted(dropped_ids)]) if dropped_ids else "Unknown"
            icmp_desc = (
                f"RFC 791 / RFC 792 Protocol Action: Reassembly timer expired after {timeout_seconds:.1f}s. "
                f"Missing byte hole(s): {missing_ranges_str} due to lost Fragment(s) {lost_ids_str}. "
                f"The destination host discarded all {buffered_bytes} partially buffered bytes "
                f"and transmitted an ICMP Time Exceeded (Type 11, Code 1 — Fragment Reassembly Time Exceeded) "
                f"message to the Source Host. The entire original datagram ({total_payload + IPV4_HEADER_SIZE} B) was lost "
                f"and must be retransmitted end-to-end by Layer 4 (TCP) or the application."
            )
        
        return ReassemblySimulationResult(
            success=is_success,
            original_payload=total_payload,
            reassembled_payload=buffered_bytes if is_success else 0,
            total_fragments_sent=len(all_frags),
            fragments_received=received_frags,
            dropped_fragments=dropped_frags,
            arrival_order_name=order_name,
            arrival_sequence=arrival_sequence,
            final_holes=final_holes,
            events=events,
            icmp_generated=icmp_gen,
            icmp_type=11,
            icmp_code=1,
            icmp_name="ICMP Type 11, Code 1: Fragment Reassembly Time Exceeded",
            icmp_description=icmp_desc,
            timeout_seconds=timeout_seconds,
        )

    @staticmethod
    def export_fragments_csv(result: FragmentationResult) -> str:
        """Export fragment details to CSV string."""
        if not result.fragments:
            return ""
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(result.fragments[0].to_dict().keys()))
        writer.writeheader()
        for frag in result.fragments:
            writer.writerow(frag.to_dict())
        
        return output.getvalue()

    @staticmethod
    def export_measurements_csv(measurements: List[Dict]) -> str:
        """Export experiment measurements to CSV string."""
        if not measurements:
            return ""
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(measurements[0].keys()))
        writer.writeheader()
        for row in measurements:
            writer.writerow(row)
        
        return output.getvalue()


# ─── Terminal-mode runner (reference implementation) ──────────────
def run_terminal_demo():
    """Run the simulation in terminal mode for validation."""
    engine = FragmentationEngine()
    
    print("=" * 70)
    print("  NetVista 3D — IPv4 Fragmentation Simulator (Terminal Mode)")
    print("  Student ID: 25CS052 | Advanced Group")
    print("=" * 70)
    
    # Test case: 4000-byte payload through [1500, 620, 400]
    payload = 4000
    mtu_path = [1500, 620, 400]
    
    print(f"\n📦 Original Payload: {payload} bytes")
    print(f"🔗 MTU Path: {' → '.join(map(str, mtu_path))}")
    print(f"📐 IPv4 Header: {IPV4_HEADER_SIZE} bytes")
    print(f"📊 Original Packet Total: {payload + IPV4_HEADER_SIZE} bytes")
    print("-" * 70)
    
    result = engine.fragment_packet(payload, mtu_path)
    
    if result.error:
        print(f"\n❌ Error: {result.error}")
        return
    
    print(f"\n{'#':>3} {'Hop':>4} {'MTU':>6} {'Payload':>8} {'Header':>7} {'Total':>6} "
          f"{'ByteOff':>8} {'Off/8':>6} {'MF':>3} {'Range':>15}")
    print("-" * 70)
    
    for f in result.fragments:
        print(f"{f.fragment_id:>3} {f.hop:>4} {f.mtu_at_hop:>6} {f.payload_size:>8} "
              f"{f.header_size:>7} {f.total_size:>6} {f.byte_offset:>8} "
              f"{f.offset_in_units:>6} {f.mf_flag:>3} "
              f"{f.payload_range[0]:>6}–{f.payload_range[1]:<6}")
    
    print("-" * 70)
    print(f"Total Fragments: {result.total_fragments}")
    print(f"Total Header Overhead: {result.total_header_overhead} bytes")
    print(f"Overhead Percentage: {result.overhead_percentage:.2f}%")
    print(f"Total Bytes Transmitted: {result.total_bytes_transmitted}")
    
    # Validation
    print("\n" + "=" * 70)
    print("  VALIDATION CHECKS")
    print("=" * 70)
    validation = engine.validate_fragments(result)
    for check in validation.checks:
        status = "✅" if check["passed"] else "❌"
        print(f"  {check['name']}")
        print(f"    {check['detail']}")
    
    print(f"\n  Overall: {'ALL CHECKS PASSED ✅' if validation.is_valid else 'SOME CHECKS FAILED ❌'}")
    
    # DF flag demo
    print("\n" + "=" * 70)
    print("  DON'T FRAGMENT (DF) FLAG TEST")
    print("=" * 70)
    df_result = engine.fragment_packet(payload, mtu_path, df_flag=True)
    if df_result.error:
        print(f"  {df_result.error}")


if __name__ == "__main__":
    run_terminal_demo()
