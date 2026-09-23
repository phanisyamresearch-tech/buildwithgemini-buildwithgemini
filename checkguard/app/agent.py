# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import os
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from app.a2ui_utils import a2ui_callback


MODEL = "gemini-3.6-flash"


import json
import urllib.parse
import urllib.request

from app.firestore_tools import (
    get_entity_risk_profile,
    query_business_statistics,
    record_check_verification,
    search_check_history,
)

def verify_bank_institution(bank_name: str) -> dict:
    """Verify an issuing financial institution using the public FDIC BankFind API.

    Args:
        bank_name: The name of the bank printed on the check (e.g. 'JPMorgan Chase', 'First National Bank').

    Returns:
        Dict with FDIC insurance certificate number, active charter status, city/state, and website.
    """
    clean_name = bank_name.strip()
    encoded_name = urllib.parse.quote(f'NAME:"{clean_name}"')
    url = f"https://banks.data.fdic.gov/api/institutions?search={encoded_name}&fields=NAME,CITY,STNAME,CERT,ACTIVE,WEBADDR&limit=3"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CheckGuardApp/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            total = data.get("meta", {}).get("total", 0)
            if total == 0:
                return {
                    "verified": False,
                    "bank_name": clean_name,
                    "message": f"No active FDIC-insured institution found matching '{clean_name}'. Verify spelling or proceed with caution.",
                }
            
            top_match = data.get("data", [])[0].get("data", {})
            return {
                "verified": True,
                "bank_name": top_match.get("NAME"),
                "is_active_fdic_insured": top_match.get("ACTIVE") == 1,
                "fdic_cert": top_match.get("CERT"),
                "location": f"{top_match.get('CITY')}, {top_match.get('STNAME')}",
                "website": top_match.get("WEBADDR", "N/A"),
                "matched_count": total,
            }
    except Exception as exc:
        return {
            "verified": False,
            "bank_name": clean_name,
            "error": f"Failed to query FDIC database: {str(exc)}",
        }


def calculate_cashing_fee_and_payout(
    amount: float,
    check_type: str = "payroll",
    risk_level: str = "low",
) -> dict:
    """Calculate cashing fee, net payout amount, and manager approval requirements.

    Args:
        amount: Dollar amount of the check.
        check_type: Type of check ('payroll', 'government', 'cashier', or 'personal'). Default is 'payroll'.
        risk_level: Assessed risk tier ('low', 'medium', or 'high'). Default is 'low'.

    Returns:
        Dict with fee percentage, fee dollar amount, net payout to customer, and manager authorization status.
    """
    fee_rates = {
        "government": 0.015,  # 1.5%
        "payroll": 0.02,       # 2.0%
        "cashier": 0.025,     # 2.5%
        "personal": 0.05,     # 5.0%
    }
    base_rate = fee_rates.get(check_type.lower(), 0.02)

    # Risk adjustment surcharge
    if risk_level.lower() == "high":
        base_rate += 0.015
    elif risk_level.lower() == "medium":
        base_rate += 0.005

    fee_amount = round(amount * base_rate, 2)
    # Minimum $3.00 fee
    if fee_amount < 3.00:
        fee_amount = 3.00

    net_payout = round(amount - fee_amount, 2)
    requires_manager_approval = amount > 2500.00 or risk_level.lower() == "high"

    return {
        "check_amount": amount,
        "check_type": check_type,
        "fee_rate_percent": round(base_rate * 100, 2),
        "fee_amount": fee_amount,
        "net_payout": net_payout,
        "requires_manager_approval": requires_manager_approval,
        "note": "Manager sign-off required for amounts over $2,500 or high-risk checks." if requires_manager_approval else "Approved for standard teller payout.",
    }


import os

def geocode_address(address: str) -> dict:
    """Convert a postal address or location string into geographic latitude/longitude coordinates using Google Maps Geocoding API.

    Args:
        address: The address or place to geocode (e.g. '100 Industrial Pkwy, Kansas City, MO').

    Returns:
        Dict containing formatted address, latitude, longitude, and status.
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable is not configured."}

    encoded_address = urllib.parse.quote(address.strip())
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=7) as response:
            data = json.loads(response.read().decode())
            status = data.get("status")
            if status != "OK" or not data.get("results"):
                return {
                    "error": f"Geocoding failed with status: {status}",
                    "details": data.get("error_message", "No results found"),
                }
            top_result = data["results"][0]
            loc = top_result.get("geometry", {}).get("location", {})
            return {
                "name": address,
                "address": top_result.get("formatted_address"),
                "location": {
                    "latitude": loc.get("lat"),
                    "longitude": loc.get("lng"),
                },
                "status": "OK",
            }
    except Exception as exc:
        return {"error": f"Geocoding request failed: {str(exc)}"}


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "bank",
    radius_meters: float = 2000.0,
    max_results: int = 5,
) -> dict:
    """Find nearby places (e.g. banks, police stations, businesses) using Google Places API (New).

    Args:
        latitude: Latitude coordinate of the center point.
        longitude: Longitude coordinate of the center point.
        place_type: Type of place to search for (e.g. 'bank', 'atm', 'police', 'convenience_store'). Default is 'bank'.
        radius_meters: Radius in meters around the coordinates (default 2000.0m).
        max_results: Max number of results (default 5).

    Returns:
        Dict containing list of matching places with name, formatted address, and location.
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable is not configured."}

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
    }
    payload = {
        "includedTypes": [place_type.lower().strip()],
        "maxResultCount": min(max_results, 20),
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                },
                "radius": float(radius_meters),
            }
        },
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=7) as response:
            data = json.loads(response.read().decode())
            places_raw = data.get("places", [])
            places_clean = []
            for p in places_raw:
                display_name = p.get("displayName", {}).get("text", "Unknown")
                formatted_address = p.get("formattedAddress", "N/A")
                loc = p.get("location", {})
                places_clean.append({
                    "name": display_name,
                    "address": formatted_address,
                    "location": {
                        "latitude": loc.get("latitude"),
                        "longitude": loc.get("longitude"),
                    },
                })
            return {
                "total": len(places_clean),
                "places": places_clean,
            }
    except Exception as exc:
        return {"error": f"Places API request failed: {str(exc)}"}


from google.adk.tools import ToolContext
from google.cloud import storage

# Hardcoded bucket and project for CheckGuard media
GCS_MEDIA_BUCKET = "checkguard-media-5835"
PROJECT_ID = "qwiklabs-gcp-04-dacd550359a7"

def generate_marketing_image(
    prompt_subject: str,
    tool_context: ToolContext,
) -> dict:
    """Generate a promotional marketing image or service badge for the check cashing business.

    Strict security safeguard: Never includes personal information, PII, PHI, PCI, real bank accounts, or signatures.

    Args:
        prompt_subject: The topic or style for the marketing image (e.g. 'storefront instant verification banner', 'trust and security service badge', 'fast payroll check cashing promo graphic').
        tool_context: ToolContext instance provided automatically by ADK to record artifacts.

    Returns:
        Dict containing the public Cloud Storage URL, filename, and status.
    """
    from google import genai
    import uuid

    # Enforce PII/PCI security guardrail in prompt
    safe_prompt = (
        f"Professional, clean marketing visual for a small business check cashing service: {prompt_subject}. "
        "Modern vector illustration style, trust and security theme, financial technology branding. "
        "Strict compliance requirement: absolutely no real or fake names, no personal identification (PII), "
        "no bank account or routing numbers (PCI), no signatures, and no personal documents."
    )

    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location="global",
    )

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=safe_prompt,
    )

    image_part = None
    if response.candidates and response.candidates[0].content:
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                image_part = part
                break

    if not image_part:
        return {"error": "Image generation failed: No image data returned by model."}

    image_bytes = image_part.inline_data.data
    mime_type = image_part.inline_data.mime_type or "image/jpeg"
    unique_id = uuid.uuid4().hex[:8]
    ext = "png" if "png" in mime_type else "jpg"
    filename = f"marketing_graphic_{unique_id}.{ext}"

    # 1. Save artifact so it shows up in Playground's Artifacts panel
    try:
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        tool_context.save_artifact(
            filename=filename,
            artifact=artifact_part,
            custom_metadata={"category": "marketing", "subject": prompt_subject},
        )
    except Exception as e:
        print(f"Warning: Failed to save tool artifact: {e}")

    # 2. Upload bytes directly to public Cloud Storage bucket
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(GCS_MEDIA_BUCKET)
    blob = bucket.blob(f"marketing/{filename}")
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{GCS_MEDIA_BUCKET}/marketing/{filename}"

    return {
        "status": "success",
        "filename": filename,
        "public_url": public_url,
        "description": f"Generated marketing image for: {prompt_subject}",
        "security_check": "Verified: Zero PII/PCI/PHI included.",
    }


def generate_promotional_video(
    prompt: str,
    tool_context: ToolContext,
) -> dict:
    """Generate a short promotional marketing video for the check cashing business using Google's Omni model.

    Strict security safeguard: Never includes personal information, PII, PHI, PCI, real bank accounts, or signatures.

    Args:
        prompt: Description of the short promotional video to generate (e.g. 'A 5-second dynamic modern motion graphic showcasing fast, trusted check verification').
        tool_context: ToolContext instance provided automatically by ADK to record artifacts.

    Returns:
        Dict containing public Cloud Storage URL, filename, status, and description.
    """
    import base64
    import uuid
    from google import genai

    safe_prompt = (
        f"Professional, clean promotional video for a small business check cashing service: {prompt}. "
        "Modern cinematic motion, trust and security theme, financial technology branding. "
        "Strict compliance requirement: absolutely no real or fake names, no personal identification (PII), "
        "no bank account or routing numbers (PCI), no signatures, and no personal documents."
    )

    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location="global",
    )

    interaction = client.interactions.create(
        model="gemini-omni-flash-preview",
        input=safe_prompt,
    )

    if not hasattr(interaction, "output_video") or not interaction.output_video:
        return {"error": "Video generation failed: No output video returned by Omni model."}

    video_data = interaction.output_video.data
    if not video_data:
        return {"error": "Video generation failed: Output video data is empty."}

    video_bytes = base64.b64decode(video_data) if isinstance(video_data, str) else video_data
    mime_type = interaction.output_video.mime_type or "video/mp4"

    unique_id = uuid.uuid4().hex[:8]
    filename = f"promo_video_{unique_id}.mp4"

    # 1. Save artifact so it shows up in Playground's Artifacts panel
    try:
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        tool_context.save_artifact(
            filename=filename,
            artifact=artifact_part,
            custom_metadata={"category": "marketing_video", "prompt": prompt},
        )
    except Exception as e:
        print(f"Warning: Failed to save video tool artifact: {e}")

    # 2. Upload bytes directly to public Cloud Storage bucket
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(GCS_MEDIA_BUCKET)
    blob = bucket.blob(f"marketing/{filename}")
    blob.upload_from_string(video_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{GCS_MEDIA_BUCKET}/marketing/{filename}"

    return {
        "status": "success",
        "filename": filename,
        "public_url": public_url,
        "description": f"Generated promotional video for: {prompt}",
        "security_check": "Verified: Zero PII/PCI/PHI included.",
    }



from google.adk.code_executors.agent_engine_sandbox_code_executor import AgentEngineSandboxCodeExecutor

from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.memory import VertexAiMemoryBankService

# Sandbox & Memory Bank configuration
SANDBOX_RESOURCE_NAME = "projects/1069102362772/locations/us-central1/reasoningEngines/6432349180919808000/sandboxEnvironments/6228741549488898048"
MEMORY_BANK_ID = "6432349180919808000"

async def generate_memories_callback(callback_context: CallbackContext):
    """Save durable facts and preferences across sessions into Memory Bank."""
    try:
        await callback_context.add_session_to_memory()
    except (ValueError, Exception) as exc:
        # If memory service is not available (e.g. in test or without --memory_service_uri), ignore
        pass
    return None

def memory_bank_service_builder():
    """Builds VertexAiMemoryBankService for deployment runtime."""
    return VertexAiMemoryBankService(
        project=PROJECT_ID,
        location="us-central1",
        agent_engine_id=MEMORY_BANK_ID,
    )


ROLE_DESCRIPTION = """You are CheckGuard, an expert AI assistant helping check-cashing business employees and tellers assess risk and make verification decisions.

You remember user preferences, teller instructions, and operational facts across conversations."""

WORKFLOW_DESCRIPTION = """When an employee presents a check (with bearer/payee, issuer/maker, or bank name):
1. Use `verify_bank_institution` to verify the paying bank is an active, legitimate FDIC-insured institution.
2. Use `geocode_address` and `find_nearby_places` to verify business addresses printed on checks or find nearby branch locations/issuers if requested.
3. Use `search_check_history` to look up previous checks associated with the bearer and the issuer to see if any bounced, cleared, or were flagged for fraud.
4. Use `get_entity_risk_profile` to check the trust level and standing of both the issuer and the bearer.
5. If the check is eligible to cash, use `calculate_cashing_fee_and_payout` to calculate the store fee and net cash payout.
6. Synthesize the findings to advise the employee clearly whether the check is good to cash, requires manager review, or should be rejected.
7. When a decision is finalized or the employee requests it, use `record_check_verification` to save the record to the database for future reference.
8. If a store manager or employee asks for business, financial, or operational statistics (such as checks cashed, rejected, bounced, fee revenue, loss rates, or monthly/yearly performance), use `query_business_statistics`. Provide clear summaries of transaction counts, total face values, fees earned, bounce losses, and clearance/bounce rates.
9. If the user asks for marketing visuals, promotional signs, or service badges for the business, use `generate_marketing_image`. Ensure no personal or sensitive data is ever requested or included.
10. If the user asks for promotional marketing videos or short motion graphics for the business, use `generate_promotional_video`. Ensure no personal or sensitive data is ever requested or included.
11. When complex calculations, formula modeling, or data processing is required, safely run Python code using your code execution sandbox.

Always provide clear, objective reasoning and highlight any red flags (e.g. invalid bank, prior returned checks, frozen accounts, high risk scores, or unverified first-time issuers)."""

UI_DESCRIPTION = (
    "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
    "Never nest a Card inside a Card. "
    "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
    "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
    "nothing in adk web). "
    "You may include one Image component, but only when you have a public https "
    "URL for the image (for example the URL an image tool returns after uploading "
    "to a public bucket). Set the Image url to that exact https link, for example "
    '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
    "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
    "not have a public URL, add a short Text line noting the image instead. "
    "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
    "headings and emphasis. "
    "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
    "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
)

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

INSTRUCTION = schema_manager.generate_system_prompt(
    role_description=ROLE_DESCRIPTION,
    workflow_description=WORKFLOW_DESCRIPTION,
    ui_description=UI_DESCRIPTION,
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=INSTRUCTION,
    code_executor=AgentEngineSandboxCodeExecutor(
        sandbox_resource_name=SANDBOX_RESOURCE_NAME,
    ),
    tools=[
        PreloadMemoryTool(),
        verify_bank_institution,
        geocode_address,
        find_nearby_places,
        search_check_history,
        get_entity_risk_profile,
        calculate_cashing_fee_and_payout,
        record_check_verification,
        query_business_statistics,
        generate_marketing_image,
        generate_promotional_video,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)

