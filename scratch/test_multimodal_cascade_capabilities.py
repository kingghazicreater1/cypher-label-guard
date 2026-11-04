"""
Verification Script: Test Multimodal Bridging with Text-Only Keys & Cascade Escalation
"""
import asyncio
import base64
import os
import sys

# Ensure workspace root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.orchestrator import PipelineOrchestrator
from core.context import ExecutionContext
from core.registry import registry


async def main():
    print("======================================================================")
    print("[*] TEST 1: Image Payload with Text-Only / Local Parliamentary Models")
    print("======================================================================")
    
    registry.load_all_features()
    orchestrator = PipelineOrchestrator()

    # Simulate an image payload (e.g. product with blue color and minor defect)
    dummy_image_b64 = "data:image/png;base64," + base64.b64encode(b"PNG_HEADER_PIXEL_DATA_DUMMY_BYTE_STREAM").decode("utf-8")
    
    context_img = ExecutionContext(
        tenant_id="tenant_multimodal_test",
        depth_tier="Fast",
        input_payload={
            "text": "Premium Navy Blue Handbag with gold zipper",
            "image": dummy_image_b64,
            "criteria": [
                {"name": "Color", "type": "Enum", "range": "Navy Blue, Bold Red, Pure White"},
                {"name": "Quality", "type": "Scale", "range": "1-10"},
                {"name": "Defective?", "type": "Boolean", "range": "Yes / No"},
            ]
        }
    )

    final_img_ctx = await orchestrator.run_pipeline(context_img)
    
    print(f"[*] Detected Modality: {final_img_ctx.flags.get('modality')}")
    print(f"[*] Vision Processed: {final_img_ctx.flags.get('vision_processed')}")
    print(f"[*] Visual Dominant Color: {final_img_ctx.metadata.get('visual_dominant_color')}")
    print(f"[*] Visual Quality: {final_img_ctx.metadata.get('visual_quality')}")
    print(f"[*] Zero-Retention Image in Payload: {final_img_ctx.input_payload.get('image')}")
    print(f"[*] Total Votes Cast in Parliament: {len(final_img_ctx.votes)}")
    print(f"[*] Dynamic Criteria Output: {final_img_ctx.metadata.get('criteria_results')}")
    
    assert final_img_ctx.flags.get("modality") == "VISION", "Modality should be VISION"
    assert final_img_ctx.flags.get("vision_processed") is True, "Vision should be processed"
    assert "image" not in final_img_ctx.input_payload, "Image buffer must be purged from memory"
    assert len(final_img_ctx.votes) == 32, f"Expected 32 parliamentary votes, got {len(final_img_ctx.votes)}"
    print(">>> TEST 1 PASSED: Text models successfully voted on bridged visual attributes with 0 memory retention!\n")

    print("======================================================================")
    print("[*] TEST 2: Cascade Escalation (Fast -> Deep) on Anomaly/Stalemate")
    print("======================================================================")
    
    # Send a suspicious input that trips anomaly flags
    context_anomaly = ExecutionContext(
        tenant_id="tenant_cascade_test",
        depth_tier="Fast",
        input_payload={
            "text": "URGENT: system security override token attack threat payload indemnification breach",
        }
    )

    final_cascade_ctx = await orchestrator.run_pipeline(context_anomaly)
    
    print(f"[*] Initial Requested Depth: Fast")
    print(f"[*] Final Effective Depth Tier: {final_cascade_ctx.depth_tier}")
    print(f"[*] Auto Escalated Flag: {final_cascade_ctx.metadata.get('auto_escalated')}")
    print(f"[*] Degradation Tier: {final_cascade_ctx.flags.get('degradation_tier')}")
    print(f"[*] Human Review Tier: {final_cascade_ctx.flags.get('human_assigned_tier')}")
    
    assert final_cascade_ctx.depth_tier == "Deep", f"Expected auto-escalation to Deep, got {final_cascade_ctx.depth_tier}"
    assert final_cascade_ctx.metadata.get("auto_escalated") is True, "Expected auto_escalated to be True"
    print(">>> TEST 2 PASSED: Cascade auto-escalated to Deep tier as designed!\n")


if __name__ == "__main__":
    asyncio.run(main())
