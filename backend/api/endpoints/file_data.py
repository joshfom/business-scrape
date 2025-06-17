from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/api/file", tags=["file-data"])

# Sample business data generator for demonstration
def generate_sample_businesses(count: int = 1000) -> List[Dict[str, Any]]:
    """Generate sample business data for testing"""
    
    domains = ["yello.ae", "surinamyp.com", "businesslist.co.ke", "businesslist.com.ng", "brazilyello.com"]
    cities = {
        "yello.ae": ["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Fujairah"],
        "surinamyp.com": ["Paramaribo", "Nieuw Nickerie", "Moengo", "Albina", "Groningen"],
        "businesslist.co.ke": ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret"],
        "businesslist.com.ng": ["Lagos", "Abuja", "Kano", "Ibadan", "Port Harcourt"],
        "brazilyello.com": ["São Paulo", "Rio de Janeiro", "Brasília", "Salvador", "Fortaleza"]
    }
    
    categories = [
        "Business Services", "Restaurants", "Healthcare", "Technology", "Retail",
        "Construction", "Education", "Finance", "Real Estate", "Transportation",
        "Manufacturing", "Tourism", "Legal Services", "Consulting", "Media"
    ]
    
    businesses = []
    
    for i in range(count):
        domain = random.choice(domains)
        city = random.choice(cities[domain])
        category = random.choice(categories)
        
        business = {
            "id": f"biz_{i+1:06d}",
            "name": f"{category} Company {i+1}",
            "description": f"Leading provider of {category.lower()} services in {city}",
            "phone": f"+{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000000, 9999999)}",
            "email": f"info@company{i+1}.com",
            "website": f"https://company{i+1}.com",
            "address": f"{random.randint(1, 999)} Business Street, {city}",
            "city": city,
            "domain": domain,
            "category": category,
            "scraped_at": (datetime.now() - timedelta(days=random.randint(0, 365))).isoformat()
        }
        businesses.append(business)
    
    return businesses

# Cache for generated data
_cached_businesses = None
_cache_timestamp = None
CACHE_DURATION = 3600  # 1 hour

def get_businesses_data() -> List[Dict[str, Any]]:
    """Get businesses data with caching"""
    global _cached_businesses, _cache_timestamp
    
    current_time = datetime.now().timestamp()
    
    if _cached_businesses is None or (current_time - _cache_timestamp) > CACHE_DURATION:
        # Generate larger dataset for testing
        _cached_businesses = generate_sample_businesses(100000)  # 100K records for testing
        _cache_timestamp = current_time
    
    return _cached_businesses

def filter_businesses(
    businesses: List[Dict[str, Any]],
    domain: Optional[str] = None,
    city: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Filter businesses based on criteria"""
    
    filtered = businesses
    
    if domain:
        filtered = [b for b in filtered if b["domain"].lower() == domain.lower()]
    
    if city:
        filtered = [b for b in filtered if b["city"].lower() == city.lower()]
    
    if category:
        filtered = [b for b in filtered if category.lower() in b["category"].lower()]
    
    if search:
        search_lower = search.lower()
        filtered = [
            b for b in filtered 
            if search_lower in b["name"].lower() 
            or search_lower in b["description"].lower()
            or search_lower in b["category"].lower()
        ]
    
    return filtered

def sort_businesses(
    businesses: List[Dict[str, Any]], 
    sort_by: str = "name", 
    sort_order: str = "asc"
) -> List[Dict[str, Any]]:
    """Sort businesses by specified field"""
    
    valid_sort_fields = ["name", "city", "domain", "category", "scraped_at"]
    if sort_by not in valid_sort_fields:
        sort_by = "name"
    
    reverse = sort_order.lower() == "desc"
    
    try:
        if sort_by == "scraped_at":
            return sorted(businesses, key=lambda x: x[sort_by], reverse=reverse)
        else:
            return sorted(businesses, key=lambda x: x[sort_by].lower(), reverse=reverse)
    except (KeyError, AttributeError):
        return businesses

@router.get("/businesses")
async def get_file_businesses(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=1000, description="Items per page"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    city: Optional[str] = Query(None, description="Filter by city"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in name, description, category"),
    sort_by: str = Query("name", description="Sort by field (name, city, domain, category, scraped_at)"),
    sort_order: str = Query("asc", description="Sort order (asc, desc)")
):
    """
    Get businesses from file data with pagination, filtering, and sorting.
    Optimized for large datasets (up to 1M+ records).
    """
    
    try:
        # Get all businesses data
        all_businesses = get_businesses_data()
        
        # Apply filters
        filtered_businesses = filter_businesses(
            all_businesses, domain, city, category, search
        )
        
        # Apply sorting
        sorted_businesses = sort_businesses(filtered_businesses, sort_by, sort_order)
        
        # Calculate pagination
        total = len(sorted_businesses)
        total_pages = (total + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        # Get page data
        page_businesses = sorted_businesses[start_idx:end_idx]
        
        return {
            "businesses": page_businesses,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "filters_applied": {
                "domain": domain,
                "city": city,
                "category": category,
                "search": search,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.get("/stats")
async def get_file_stats():
    """Get statistics about the file-based business data"""
    
    try:
        businesses = get_businesses_data()
        
        # Calculate statistics
        total_businesses = len(businesses)
        domains = {}
        cities = {}
        categories = {}
        
        for business in businesses:
            domain = business["domain"]
            city = business["city"]
            category = business["category"]
            
            domains[domain] = domains.get(domain, 0) + 1
            cities[city] = cities.get(city, 0) + 1
            categories[category] = categories.get(category, 0) + 1
        
        return {
            "total_businesses": total_businesses,
            "total_domains": len(domains),
            "total_cities": len(cities),
            "total_categories": len(categories),
            "businesses_by_domain": domains,
            "top_cities": dict(sorted(cities.items(), key=lambda x: x[1], reverse=True)[:10]),
            "top_categories": dict(sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]),
            "data_source": "file-based",
            "last_updated": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@router.get("/domains")
async def get_file_domains():
    """Get list of domains with business counts"""
    
    try:
        businesses = get_businesses_data()
        domains = {}
        
        for business in businesses:
            domain = business["domain"]
            if domain not in domains:
                domains[domain] = {
                    "domain": domain,
                    "business_count": 0,
                    "last_scraped": business["scraped_at"]
                }
            domains[domain]["business_count"] += 1
        
        return {
            "domains": list(domains.values())
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting domains: {str(e)}")

@router.get("/cities")
async def get_file_cities(
    domain: Optional[str] = Query(None, description="Filter cities by domain")
):
    """Get list of cities with business counts, optionally filtered by domain"""
    
    try:
        businesses = get_businesses_data()
        
        if domain:
            businesses = [b for b in businesses if b["domain"].lower() == domain.lower()]
        
        cities = {}
        for business in businesses:
            city_key = (business["city"], business["domain"])
            if city_key not in cities:
                cities[city_key] = {
                    "city": business["city"],
                    "domain": business["domain"],
                    "business_count": 0
                }
            cities[city_key]["business_count"] += 1
        
        return {
            "cities": list(cities.values())
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cities: {str(e)}")

@router.get("/categories")
async def get_file_categories(
    domain: Optional[str] = Query(None, description="Filter categories by domain")
):
    """Get list of categories with business counts, optionally filtered by domain"""
    
    try:
        businesses = get_businesses_data()
        
        if domain:
            businesses = [b for b in businesses if b["domain"].lower() == domain.lower()]
        
        categories = {}
        for business in businesses:
            category = business["category"]
            if category not in categories:
                categories[category] = {
                    "category": category,
                    "business_count": 0
                }
            categories[category]["business_count"] += 1
        
        return {
            "categories": sorted(categories.values(), key=lambda x: x["business_count"], reverse=True)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting categories: {str(e)}")

@router.post("/refresh-data")
async def refresh_file_data():
    """Refresh the cached business data"""
    
    global _cached_businesses, _cache_timestamp
    _cached_businesses = None
    _cache_timestamp = None
    
    # Regenerate data
    get_businesses_data()
    
    return {
        "message": "Data refreshed successfully",
        "total_records": len(_cached_businesses),
        "timestamp": datetime.now().isoformat()
    }
