from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from models.database import database
from bson.objectid import ObjectId
import logging
from datetime import datetime
from fastapi.responses import JSONResponse
import math

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public", tags=["Public API"])

# Response models for better documentation
from pydantic import BaseModel, Field
from typing import Union

class PaginationInfo(BaseModel):
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

class BusinessPublic(BaseModel):
    id: str = Field(..., description="Business unique identifier")
    name: str = Field(..., description="Business name")
    title: Optional[str] = Field(None, description="Business title")
    category: Optional[str] = Field(None, description="Business category")
    city: str = Field(..., description="City where business is located")
    country: str = Field(..., description="Country where business is located")
    address: Optional[str] = Field(None, description="Business address")
    phone: Optional[str] = Field(None, description="Business phone number")
    mobile: Optional[str] = Field(None, description="Business mobile number")
    website: Optional[str] = Field(None, description="Business website")
    coordinates: Optional[Dict[str, float]] = Field(None, description="Latitude and longitude coordinates")
    rating: Optional[float] = Field(None, description="Business rating (1-5)")
    reviews_count: Optional[int] = Field(None, description="Number of reviews")
    established_year: Optional[int] = Field(None, description="Year business was established")
    employees: Optional[str] = Field(None, description="Number of employees")
    description: Optional[str] = Field(None, description="Business description")
    tags: Optional[List[str]] = Field(None, description="Business tags/categories")
    working_hours: Optional[Dict[str, str]] = Field(None, description="Working hours by day")
    domain: str = Field(..., description="Source domain where data was scraped")
    scraped_at: str = Field(..., description="When the data was scraped (ISO format)")

class BusinessListResponse(BaseModel):
    data: List[BusinessPublic] = Field(..., description="List of businesses")
    pagination: PaginationInfo = Field(..., description="Pagination information")
    filters_applied: Dict[str, Any] = Field(..., description="Filters that were applied")

class StatsResponse(BaseModel):
    total_businesses: int = Field(..., description="Total number of businesses in database")
    unique_cities: int = Field(..., description="Number of unique cities")
    unique_countries: int = Field(..., description="Number of unique countries")
    unique_categories: int = Field(..., description="Number of unique categories")
    unique_domains: int = Field(..., description="Number of unique domains")
    last_updated: str = Field(..., description="Last update timestamp")

class DomainsResponse(BaseModel):
    domains: List[str] = Field(..., description="List of available domains")
    total_count: int = Field(..., description="Total number of domains")

class CitiesResponse(BaseModel):
    cities: List[Dict[str, Any]] = Field(..., description="List of cities with business counts")
    total_count: int = Field(..., description="Total number of cities")

@router.get("/businesses", 
           response_model=BusinessListResponse,
           summary="Get businesses with pagination",
           description="Retrieve a paginated list of businesses with optional filtering")
async def get_businesses_public(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page (max 100)"),
    city: Optional[str] = Query(None, description="Filter by city name (case-insensitive)"),
    country: Optional[str] = Query(None, description="Filter by country name (case-insensitive)"),
    category: Optional[str] = Query(None, description="Filter by business category (case-insensitive)"),
    domain: Optional[str] = Query(None, description="Filter by source domain"),
    search: Optional[str] = Query(None, description="Search in business name, title, or description"),
    has_phone: Optional[bool] = Query(None, description="Filter businesses that have phone numbers"),
    has_website: Optional[bool] = Query(None, description="Filter businesses that have websites"),
    has_coordinates: Optional[bool] = Query(None, description="Filter businesses that have location coordinates"),
    min_rating: Optional[float] = Query(None, ge=1, le=5, description="Minimum rating filter"),
    sort_by: Optional[str] = Query("scraped_at", description="Sort by field: name, city, category, rating, scraped_at"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc")
):
    """
    Get a paginated list of businesses with comprehensive filtering options.
    
    This endpoint provides access to scraped business data with:
    - Pagination support
    - Multiple filter options
    - Sorting capabilities
    - Full business details
    
    **Rate Limiting**: This endpoint is rate-limited to prevent abuse.
    """
    try:
        db = database.get_database()
        businesses_collection = db.businesses
        
        # Build filter query
        filter_query = {}
        filters_applied = {}
        
        if city:
            filter_query["city"] = {"$regex": city, "$options": "i"}
            filters_applied["city"] = city
            
        if country:
            filter_query["country"] = {"$regex": country, "$options": "i"}
            filters_applied["country"] = country
            
        if category:
            filter_query["category"] = {"$regex": category, "$options": "i"}
            filters_applied["category"] = category
            
        if domain:
            filter_query["domain"] = domain
            filters_applied["domain"] = domain
            
        if search:
            filter_query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"title": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
            filters_applied["search"] = search
            
        if has_phone is not None:
            if has_phone:
                filter_query["phone"] = {"$exists": True, "$ne": None, "$ne": ""}
            else:
                filter_query["$or"] = [
                    {"phone": {"$exists": False}},
                    {"phone": None},
                    {"phone": ""}
                ]
            filters_applied["has_phone"] = has_phone
            
        if has_website is not None:
            if has_website:
                filter_query["website"] = {"$exists": True, "$ne": None, "$ne": ""}
            else:
                filter_query["$or"] = [
                    {"website": {"$exists": False}},
                    {"website": None},
                    {"website": ""}
                ]
            filters_applied["has_website"] = has_website
            
        if has_coordinates is not None:
            if has_coordinates:
                filter_query["coordinates"] = {"$exists": True, "$ne": None}
            else:
                filter_query["$or"] = [
                    {"coordinates": {"$exists": False}},
                    {"coordinates": None}
                ]
            filters_applied["has_coordinates"] = has_coordinates
            
        if min_rating is not None:
            filter_query["rating"] = {"$gte": min_rating}
            filters_applied["min_rating"] = min_rating
        
        # Calculate pagination
        skip = (page - 1) * limit
        
        # Get total count
        total_items = await businesses_collection.count_documents(filter_query)
        total_pages = math.ceil(total_items / limit) if total_items > 0 else 1
        
        # Build sort query
        sort_direction = 1 if sort_order.lower() == "asc" else -1
        sort_query = [(sort_by, sort_direction)]
        
        # Get businesses
        cursor = businesses_collection.find(filter_query).sort(sort_query).skip(skip).limit(limit)
        businesses = []
        
        async for business in cursor:
            # Convert to public format
            business_data = {
                "id": str(business["_id"]),
                "name": business.get("name", ""),
                "title": business.get("title"),
                "category": business.get("category"),
                "city": business.get("city", ""),
                "country": business.get("country", ""),
                "address": business.get("address"),
                "phone": business.get("phone"),
                "mobile": business.get("mobile"),
                "website": business.get("website"),
                "coordinates": business.get("coordinates"),
                "rating": business.get("rating"),
                "reviews_count": business.get("reviews_count"),
                "established_year": business.get("established_year"),
                "employees": business.get("employees"),
                "description": business.get("description"),
                "tags": business.get("tags"),
                "working_hours": business.get("working_hours"),
                "domain": business.get("domain", ""),
                "scraped_at": business.get("scraped_at", datetime.utcnow()).isoformat() if isinstance(business.get("scraped_at"), datetime) else business.get("scraped_at", "")
            }
            businesses.append(business_data)
        
        # Build pagination info
        pagination = {
            "page": page,
            "limit": limit,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
        return {
            "data": businesses,
            "pagination": pagination,
            "filters_applied": filters_applied
        }
        
    except Exception as e:
        logger.error(f"Error getting public businesses: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/businesses/{business_id}",
           response_model=BusinessPublic,
           summary="Get a specific business by ID",
           description="Retrieve detailed information for a specific business")
async def get_business_public(business_id: str):
    """
    Get detailed information for a specific business by its ID.
    
    Returns all available information about the business including:
    - Contact details
    - Location information
    - Business metrics
    - Source information
    """
    try:
        db = database.get_database()
        businesses_collection = db.businesses
        
        business = await businesses_collection.find_one({"_id": ObjectId(business_id)})
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        
        # Convert to public format
        business_data = {
            "id": str(business["_id"]),
            "name": business.get("name", ""),
            "title": business.get("title"),
            "category": business.get("category"),
            "city": business.get("city", ""),
            "country": business.get("country", ""),
            "address": business.get("address"),
            "phone": business.get("phone"),
            "mobile": business.get("mobile"),
            "website": business.get("website"),
            "coordinates": business.get("coordinates"),
            "rating": business.get("rating"),
            "reviews_count": business.get("reviews_count"),
            "established_year": business.get("established_year"),
            "employees": business.get("employees"),
            "description": business.get("description"),
            "tags": business.get("tags"),
            "working_hours": business.get("working_hours"),
            "domain": business.get("domain", ""),
            "scraped_at": business.get("scraped_at", datetime.utcnow()).isoformat() if isinstance(business.get("scraped_at"), datetime) else business.get("scraped_at", "")
        }
        
        return business_data
        
    except Exception as e:
        logger.error(f"Error getting business {business_id}: {e}")
        if "invalid ObjectId" in str(e).lower():
            raise HTTPException(status_code=400, detail="Invalid business ID format")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/stats",
           response_model=StatsResponse,
           summary="Get database statistics",
           description="Get overall statistics about the business database")
async def get_stats_public():
    """
    Get comprehensive statistics about the business database.
    
    Returns summary information including:
    - Total number of businesses
    - Unique cities, countries, categories
    - Data freshness information
    """
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
                    "unique_countries": {"$addToSet": "$country"},
                    "unique_categories": {"$addToSet": "$category"},
                    "unique_domains": {"$addToSet": "$domain"},
                    "latest_scrape": {"$max": "$scraped_at"}
                }
            }
        ]
        
        result = await businesses_collection.aggregate(pipeline).to_list(length=1)
        
        if result:
            stats = result[0]
            return {
                "total_businesses": stats.get("total_businesses", 0),
                "unique_cities": len(stats.get("unique_cities", [])),
                "unique_countries": len(stats.get("unique_countries", [])),
                "unique_categories": len(stats.get("unique_categories", [])),
                "unique_domains": len(stats.get("unique_domains", [])),
                "last_updated": stats.get("latest_scrape", datetime.utcnow()).isoformat() if isinstance(stats.get("latest_scrape"), datetime) else str(stats.get("latest_scrape", ""))
            }
        else:
            return {
                "total_businesses": 0,
                "unique_cities": 0,
                "unique_countries": 0,
                "unique_categories": 0,
                "unique_domains": 0,
                "last_updated": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error getting public stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/domains",
           response_model=DomainsResponse,
           summary="Get available domains",
           description="Get list of all domains that have business data")
async def get_domains_public():
    """
    Get a list of all domains that contain business data.
    
    Useful for understanding data sources and filtering by domain.
    """
    try:
        db = database.get_database()
        businesses_collection = db.businesses
        
        domains = await businesses_collection.distinct("domain")
        domains = [d for d in domains if d]  # Remove null/empty domains
        
        return {
            "domains": sorted(domains),
            "total_count": len(domains)
        }
        
    except Exception as e:
        logger.error(f"Error getting domains: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/cities",
           response_model=CitiesResponse,
           summary="Get cities with business counts",
           description="Get list of all cities with the number of businesses in each")
async def get_cities_public(
    country: Optional[str] = Query(None, description="Filter cities by country"),
    min_businesses: Optional[int] = Query(None, ge=1, description="Minimum number of businesses in city")
):
    """
    Get a list of all cities with business counts.
    
    Optionally filter by country or minimum business count.
    """
    try:
        db = database.get_database()
        businesses_collection = db.businesses
        
        # Build aggregation pipeline
        pipeline = []
        
        # Add country filter if specified
        if country:
            pipeline.append({
                "$match": {"country": {"$regex": country, "$options": "i"}}
            })
        
        # Group by city and country, count businesses
        pipeline.extend([
            {
                "$group": {
                    "_id": {
                        "city": "$city",
                        "country": "$country"
                    },
                    "business_count": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "city": "$_id.city",
                    "country": "$_id.country",
                    "business_count": 1
                }
            }
        ])
        
        # Add minimum businesses filter if specified
        if min_businesses:
            pipeline.append({
                "$match": {"business_count": {"$gte": min_businesses}}
            })
        
        # Sort by business count descending
        pipeline.append({
            "$sort": {"business_count": -1}
        })
        
        cities = await businesses_collection.aggregate(pipeline).to_list(length=None)
        
        return {
            "cities": cities,
            "total_count": len(cities)
        }
        
    except Exception as e:
        logger.error(f"Error getting cities: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
