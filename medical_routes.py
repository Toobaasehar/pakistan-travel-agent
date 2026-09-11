"""
medical_routes.py
==================
Endpoints for the "Offline Medical SOS Hub".

Design intent: every response here should be small and cacheable, so the
frontend can fetch each of these ONCE (e.g. on app load, while online)
and store the result in IndexedDB/localStorage + a Service Worker cache.
After that, the SOS Hub screen should read from that local cache first
and never block on a network request — that's what "offline-first"
actually means here.
"""

from typing import Optional, List

from fastapi import APIRouter, Query
from sqlalchemy.orm import Session

from database import SessionLocal
from models import MedicalFacility
from emergency_contacts import get_emergency_contacts
from first_aid_guides import get_first_aid_guide, FIRST_AID_GUIDES

router = APIRouter(prefix="/medical", tags=["Medical SOS"])


@router.get("/emergency-contacts")
def emergency_contacts(province: Optional[str] = None):
    """Fixed dialing numbers (Rescue 1122, Edhi, Chhipa, Tourist Police, etc.)."""
    return {"contacts": get_emergency_contacts(province)}


@router.get("/first-aid")
def first_aid_guides():
    """All first-aid guides (AMS, waterborne illness, leech/snake bites, fractures)."""
    return {"guides": FIRST_AID_GUIDES}


@router.get("/first-aid/{guide_id}")
def first_aid_guide(guide_id: str):
    """A single first-aid guide by id, e.g. 'ams' or 'snake_bite'."""
    guide = get_first_aid_guide(guide_id)
    if guide is None:
        return {"error": f"No first-aid guide found for id '{guide_id}'."}
    return guide


@router.get("/facilities")
def list_facilities(
    province: Optional[str] = None,
    district: Optional[str] = None,
    facility_type: Optional[str] = None,
    has_anti_venom: Optional[bool] = None,
    has_anti_rabies: Optional[bool] = None,
):
    """
    Remote Area Medical Locator. Filters are all optional so the frontend
    can either pull the FULL table once (for offline caching) or ask a
    narrower question when online (e.g. "anti-venom near Chitral").
    """
    db: Session = SessionLocal()
    try:
        query = db.query(MedicalFacility)
        if province:
            query = query.filter(MedicalFacility.province.ilike(f"%{province}%"))
        if district:
            query = query.filter(MedicalFacility.district.ilike(f"%{district}%"))
        if facility_type:
            query = query.filter(MedicalFacility.facility_type.ilike(f"%{facility_type}%"))
        if has_anti_venom is not None:
            query = query.filter(MedicalFacility.has_anti_venom == has_anti_venom)
        if has_anti_rabies is not None:
            query = query.filter(MedicalFacility.has_anti_rabies == has_anti_rabies)

        results = query.all()
        return {
            "count": len(results),
            "facilities": [
                {
                    "id": f.id,
                    "name": f.name,
                    "facility_type": f.facility_type,
                    "province": f.province,
                    "district": f.district,
                    "latitude": f.latitude,
                    "longitude": f.longitude,
                    "contact_number": f.contact_number,
                    "is_24_7": f.is_24_7,
                    "has_anti_venom": f.has_anti_venom,
                    "has_anti_rabies": f.has_anti_rabies,
                    "has_trauma_care": f.has_trauma_care,
                    "notes": f.notes,
                }
                for f in results
            ],
        }
    finally:
        db.close()


@router.get("/bundle")
def offline_bundle():
    """
    Single combined payload: everything the SOS Hub needs for full offline
    operation in one request (facilities + contacts + guides). Intended
    to be fetched once and cached — this is the endpoint the frontend's
    Service Worker should call to warm the offline cache.
    """
    facilities_response = list_facilities()
    return {
        "facilities": facilities_response["facilities"],
        "emergency_contacts": get_emergency_contacts(),
        "first_aid_guides": FIRST_AID_GUIDES,
    }
