from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from models.schemas import BusinessData, ExportRequest, ExportMode, JobStats
from models.database import database
from bson.objectid import ObjectId
import logging
import json
from fastapi.responses import StreamingResponse
from datetime import datetime
import io

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/businesses", tags=["businesses"])

@router.get("/", response_model=List[dict])
async def list_businesses(
    skip: int = 0, 
    limit: int = 50,
    domain: Optional[str] = None,
    city: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """List businesses with optional filtering"""
    try:
        db = database.get_database()
        businesses_collection = db.businesses
        
        # Build filter query
        filter_query = {}
        if domain:
            filter_query["domain"] = domain
        if city:
            filter_query["city"] = {"$regex": city, "$options": "i"}
        if category:
            filter_query["category"] = {"$regex": category, "$options": "i"}
        if search:
            filter_query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"title": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        
        cursor = businesses_collection.find(filter_query).sort("scraped_at", -1).skip(skip).limit(limit)
        businesses = []
        async for business in cursor:
            # Convert ObjectId to string for JSON serialization
            if '_id' in business:
                business['_id'] = str(business['_id'])
            businesses.append(business)
        
        return businesses
    except Exception as e:
        logger.error(f"Error listing businesses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{business_id}")
async def get_business(business_id: str):
    """Get a specific business by ID"""
    try:
        db = database.get_database()
        businesses_collection = db.businesses
        
        business = await businesses_collection.find_one({"_id": ObjectId(business_id)})
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        
        # Convert ObjectId to string for JSON serialization
        if '_id' in business:
            business['_id'] = str(business['_id'])
        
        return business
    except Exception as e:
        logger.error(f"Error getting business {business_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary")
async def get_business_stats():
    """Get business statistics"""
    try:
        db = database.get_database()
        businesses_collection = db.businesses
        
        # Aggregate statistics
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_businesses": {"$sum": 1},
                    "unique_cities": {"$addToSet": "$city"},
                    "unique_categories": {"$addToSet": "$category"},
                    "unique_domains": {"$addToSet": "$domain"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "total_businesses": 1,
                    "unique_cities_count": {"$size": "$unique_cities"},
                    "unique_categories_count": {"$size": "$unique_categories"},
                    "unique_domains_count": {"$size": "$unique_domains"},
                    "unique_cities": 1,
                    "unique_categories": 1,
                    "unique_domains": 1
                }
            }
        ]
        
        result = await businesses_collection.aggregate(pipeline).to_list(1)
        return result[0] if result else {
            "total_businesses": 0,
            "unique_cities_count": 0,
            "unique_categories_count": 0,
            "unique_domains_count": 0,
            "unique_cities": [],
            "unique_categories": [],
            "unique_domains": []
        }
    except Exception as e:
        logger.error(f"Error getting business stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/by-city")
async def get_businesses_by_city():
    """Get business count by city"""
    try:
        db = database.get_database()
        businesses_collection = db.businesses
        
        pipeline = [
            {
                "$group": {
                    "_id": "$city",
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"count": -1}
            },
            {
                "$limit": 20
            }
        ]
        
        result = await businesses_collection.aggregate(pipeline).to_list(20)
        return [{"city": item["_id"], "count": item["count"]} for item in result]
    except Exception as e:
        logger.error(f"Error getting businesses by city: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/by-category")
async def get_businesses_by_category():
    """Get business count by category"""
    try:
        db = database.get_database()
        businesses_collection = db.businesses
        
        pipeline = [
            {
                "$group": {
                    "_id": "$category",
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"count": -1}
            },
            {
                "$limit": 20
            }
        ]
        
        result = await businesses_collection.aggregate(pipeline).to_list(20)
        return [{"category": item["_id"], "count": item["count"]} for item in result]
    except Exception as e:
        logger.error(f"Error getting businesses by category: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/json")
async def export_businesses_json(
    domain: Optional[str] = None,
    city: Optional[str] = None,
    category: Optional[str] = None
):
    """Export businesses to JSON format"""
    try:
        db = database.get_database()
        businesses_collection = db.businesses
        
        # Build filter query
        filter_query = {}
        if domain:
            filter_query["domain"] = domain
        if city:
            filter_query["city"] = {"$regex": city, "$options": "i"}
        if category:
            filter_query["category"] = {"$regex": category, "$options": "i"}
        
        # Stream the JSON response
        async def generate_json():
            yield "["
            first = True
            async for business in businesses_collection.find(filter_query):
                if not first:
                    yield ","
                # Convert ObjectId to string and datetime to ISO format
                business["_id"] = str(business["_id"])
                if "scraped_at" in business:
                    business["scraped_at"] = business["scraped_at"].isoformat()
                yield json.dumps(business, default=str)
                first = False
            yield "]"
        
        filename = f"businesses_export_{domain or 'all'}_{city or 'all'}_{category or 'all'}.json"
        return StreamingResponse(
            generate_json(),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error exporting businesses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export/job/{job_id}")
async def export_job_businesses(job_id: str, export_request: ExportRequest):
    """Export businesses for a specific job with chunking options"""
    try:
        db = database.get_database()
        businesses_collection = db.businesses
        jobs_collection = db.scraping_jobs
        
        # Verify job exists
        job = await jobs_collection.find_one({"_id": ObjectId(job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Build filter query based on job domains
        job_domains = job.get("domains", [])
        filter_query = {"domain": {"$in": job_domains}}
        
        # Apply additional filters
        if export_request.city:
            filter_query["city"] = {"$regex": export_request.city, "$options": "i"}
        if export_request.category:
            filter_query["category"] = {"$regex": export_request.category, "$options": "i"}
        
        if export_request.chunk_by_city:
            # Export by city chunks
            return await _export_by_city_chunks(
                businesses_collection, filter_query, export_request.export_mode, job_id
            )
        else:
            # Export all businesses for this job
            return await _export_businesses_single_file(
                businesses_collection, filter_query, export_request.export_mode, 
                f"job_{job_id}_export"
            )
            
    except Exception as e:
        logger.error(f"Error exporting job businesses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}/stats")
async def get_job_business_stats(job_id: str):
    """Get business statistics for a specific job"""
    try:
        db = database.get_database()
        businesses_collection = db.businesses
        jobs_collection = db.scraping_jobs
        
        # Verify job exists
        job = await jobs_collection.find_one({"_id": ObjectId(job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job_domains = job.get("domains", [])
        filter_query = {"domain": {"$in": job_domains}}
        
        # Get total businesses for this job
        total_businesses = await businesses_collection.count_documents(filter_query)
        
        # Get exported businesses count
        exported_filter = {**filter_query, "exported_at": {"$ne": None}}
        exported_businesses = await businesses_collection.count_documents(exported_filter)
        
        # Get cities and domains for this job
        cities_pipeline = [
            {"$match": filter_query},
            {"$group": {"_id": "$city"}},
            {"$sort": {"_id": 1}}
        ]
        cities_result = await businesses_collection.aggregate(cities_pipeline).to_list(None)
        cities = [item["_id"] for item in cities_result if item["_id"]]
        
        domains_pipeline = [
            {"$match": filter_query},
            {"$group": {"_id": "$domain"}},
            {"$sort": {"_id": 1}}
        ]
        domains_result = await businesses_collection.aggregate(domains_pipeline).to_list(None)
        domains = [item["_id"] for item in domains_result if item["_id"]]
        
        # Get export summary by city
        export_summary_pipeline = [
            {"$match": exported_filter},
            {
                "$group": {
                    "_id": {
                        "city": "$city",
                        "export_mode": "$export_mode"
                    },
                    "count": {"$sum": 1},
                    "last_exported": {"$max": "$exported_at"}
                }
            }
        ]
        export_summary_result = await businesses_collection.aggregate(export_summary_pipeline).to_list(None)
        
        export_summary = {}
        for item in export_summary_result:
            city = item["_id"]["city"]
            mode = item["_id"]["export_mode"]
            if city not in export_summary:
                export_summary[city] = {}
            export_summary[city][mode] = {
                "count": item["count"],
                "last_exported": item["last_exported"].isoformat() if item["last_exported"] else None
            }
        
        return JobStats(
            job_id=job_id,
            total_businesses=total_businesses,
            exported_businesses=exported_businesses,
            cities=cities,
            domains=domains,
            export_summary=export_summary
        )
        
    except Exception as e:
        logger.error(f"Error getting job stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mark-exported")
async def mark_businesses_exported(export_request: ExportRequest):
    """Mark businesses as exported"""
    try:
        db = database.get_database()
        businesses_collection = db.businesses
        
        # Build filter query
        filter_query = {}
        if export_request.job_id:
            jobs_collection = db.scraping_jobs
            job = await jobs_collection.find_one({"_id": ObjectId(export_request.job_id)})
            if job:
                job_domains = job.get("domains", [])
                filter_query["domain"] = {"$in": job_domains}
        
        if export_request.domain:
            filter_query["domain"] = export_request.domain
        if export_request.city:
            filter_query["city"] = {"$regex": export_request.city, "$options": "i"}
        if export_request.category:
            filter_query["category"] = {"$regex": export_request.category, "$options": "i"}
        
        # Update businesses to mark as exported
        update_result = await businesses_collection.update_many(
            filter_query,
            {
                "$set": {
                    "exported_at": datetime.utcnow(),
                    "export_mode": export_request.export_mode
                }
            }
        )
        
        return {
            "message": "Businesses marked as exported",
            "updated_count": update_result.modified_count
        }
        
    except Exception as e:
        logger.error(f"Error marking businesses as exported: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _export_by_city_chunks(collection, base_filter, export_mode, job_id):
    """Export businesses grouped by city"""
    try:
        # Get all unique cities for this filter
        cities_pipeline = [
            {"$match": base_filter},
            {"$group": {"_id": "$city"}},
            {"$sort": {"_id": 1}}
        ]
        cities_result = await collection.aggregate(cities_pipeline).to_list(None)
        cities = [item["_id"] for item in cities_result if item["_id"]]
        
        # Create a ZIP file with multiple JSON files (one per city)
        import zipfile
        from io import BytesIO
        
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for city in cities:
                city_filter = {**base_filter, "city": city}
                
                # Generate JSON for this city
                city_data = []
                async for business in collection.find(city_filter):
                    business["_id"] = str(business["_id"])
                    if "scraped_at" in business:
                        business["scraped_at"] = business["scraped_at"].isoformat()
                    if "exported_at" in business and business["exported_at"]:
                        business["exported_at"] = business["exported_at"].isoformat()
                    city_data.append(business)
                
                # Add city file to ZIP
                city_filename = f"{city.replace(' ', '_').replace('/', '_')}.json"
                zip_file.writestr(city_filename, json.dumps(city_data, indent=2, default=str))
        
        zip_buffer.seek(0)
        
        filename = f"job_{job_id}_businesses_by_city.zip"
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting by city chunks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _export_businesses_single_file(collection, filter_query, export_mode, filename_prefix):
    """Export businesses to a single JSON file"""
    try:
        async def generate_json():
            yield "["
            first = True
            async for business in collection.find(filter_query):
                if not first:
                    yield ","
                # Convert ObjectId to string and datetime to ISO format
                business["_id"] = str(business["_id"])
                if "scraped_at" in business:
                    business["scraped_at"] = business["scraped_at"].isoformat()
                if "exported_at" in business and business["exported_at"]:
                    business["exported_at"] = business["exported_at"].isoformat()
                yield json.dumps(business, default=str)
                first = False
            yield "]"
        
        filename = f"{filename_prefix}_{export_mode.value}.json"
        return StreamingResponse(
            generate_json(),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting single file: {e}")
        raise HTTPException(status_code=500, detail=str(e))
