#!/usr/bin/env python3
"""
Test script to verify the complete end-to-end scraping workflow via API
"""
import asyncio
import aiohttp
import json
import time

async def test_complete_workflow():
    """Test the complete workflow via API calls"""
    base_url = "http://localhost:8000/api"
    
    async with aiohttp.ClientSession() as session:
        print("🧪 Testing Complete End-to-End Workflow")
        print("="*50)
        
        # 1. Check API health
        print("\n1️⃣ Checking API health...")
        try:
            async with session.get(f"{base_url.replace('/api', '')}/health") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ API Health: {result}")
                else:
                    print(f"❌ API Health check failed: {response.status}")
                    return
        except Exception as e:
            print(f"❌ API Health check error: {e}")
            return
        
        # 2. Get initial dashboard stats
        print("\n2️⃣ Getting initial dashboard stats...")
        try:
            async with session.get(f"{base_url}/scraping/stats") as response:
                if response.status == 200:
                    stats = await response.json()
                    print(f"✅ Initial Stats:")
                    print(f"   Total Jobs: {stats.get('total_jobs', 0)}")
                    print(f"   Active Jobs: {stats.get('active_jobs', 0)}")
                    print(f"   Total Businesses: {stats.get('total_businesses', 0)}")
                else:
                    print(f"❌ Stats fetch failed: {response.status}")
        except Exception as e:
            print(f"❌ Stats fetch error: {e}")
        
        # 3. Create a test scraping job
        print("\n3️⃣ Creating test scraping job...")
        job_data = {
            "name": "Test Pakistan Scraper - End-to-End",
            "domains": ["https://businesslist.pk"],
            "concurrent_requests": 3,
            "request_delay": 0.5
        }
        
        try:
            async with session.post(
                f"{base_url}/scraping/jobs",
                json=job_data,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    job_id = result.get('job_id')
                    print(f"✅ Job created successfully: {job_id}")
                else:
                    error_text = await response.text()
                    print(f"❌ Job creation failed: {response.status} - {error_text}")
                    return
        except Exception as e:
            print(f"❌ Job creation error: {e}")
            return
        
        # 4. Start the job
        print(f"\n4️⃣ Starting job {job_id}...")
        try:
            async with session.post(f"{base_url}/scraping/jobs/{job_id}/start") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Job started: {result.get('message')}")
                else:
                    error_text = await response.text()
                    print(f"❌ Job start failed: {response.status} - {error_text}")
                    return
        except Exception as e:
            print(f"❌ Job start error: {e}")
            return
        
        # 5. Monitor job progress for a limited time
        print(f"\n5️⃣ Monitoring job progress...")
        max_checks = 10  # Limit monitoring to prevent infinite loop
        check_count = 0
        
        while check_count < max_checks:
            try:
                async with session.get(f"{base_url}/scraping/jobs/{job_id}/status") as response:
                    if response.status == 200:
                        status = await response.json()
                        current_status = status.get('status')
                        cities_completed = status.get('cities_completed', 0)
                        businesses_scraped = status.get('businesses_scraped', 0)
                        current_city = status.get('current_city', 'N/A')
                        
                        print(f"📊 Status: {current_status} | Cities: {cities_completed} | Businesses: {businesses_scraped} | Current: {current_city}")
                        
                        # Stop monitoring if job completed or failed
                        if current_status in ['completed', 'failed', 'cancelled']:
                            print(f"🎯 Job finished with status: {current_status}")
                            break
                        
                        # If we have some businesses scraped, we can consider it working
                        if businesses_scraped > 0:
                            print(f"🎉 SUCCESS: Businesses are being scraped and saved!")
                            
                            # Pause the job to prevent excessive scraping
                            async with session.post(f"{base_url}/scraping/jobs/{job_id}/pause") as pause_response:
                                if pause_response.status == 200:
                                    print(f"⏸️  Job paused successfully")
                                else:
                                    print(f"⚠️  Could not pause job")
                            break
                        
                    else:
                        print(f"❌ Status check failed: {response.status}")
                        break
                        
            except Exception as e:
                print(f"❌ Status check error: {e}")
                break
            
            check_count += 1
            await asyncio.sleep(3)  # Wait 3 seconds between checks
        
        # 6. Get final stats
        print(f"\n6️⃣ Getting final dashboard stats...")
        try:
            async with session.get(f"{base_url}/scraping/stats") as response:
                if response.status == 200:
                    stats = await response.json()
                    print(f"✅ Final Stats:")
                    print(f"   Total Jobs: {stats.get('total_jobs', 0)}")
                    print(f"   Active Jobs: {stats.get('active_jobs', 0)}")
                    print(f"   Total Businesses: {stats.get('total_businesses', 0)}")
                    print(f"   Businesses Today: {stats.get('businesses_today', 0)}")
                else:
                    print(f"❌ Final stats fetch failed: {response.status}")
        except Exception as e:
            print(f"❌ Final stats fetch error: {e}")
        
        # 7. List some businesses to verify they were saved
        print(f"\n7️⃣ Checking saved businesses...")
        try:
            async with session.get(f"{base_url}/businesses?limit=3") as response:
                if response.status == 200:
                    businesses = await response.json()
                    print(f"✅ Found {len(businesses)} businesses in database:")
                    for i, business in enumerate(businesses[:3], 1):
                        print(f"   {i}. {business.get('name', 'N/A')} - {business.get('city', 'N/A')}, {business.get('country', 'N/A')}")
                else:
                    print(f"❌ Businesses fetch failed: {response.status}")
        except Exception as e:
            print(f"❌ Businesses fetch error: {e}")
        
        print(f"\n{'='*50}")
        print(f"🎯 End-to-End Test Complete!")
        print(f"{'='*50}")

if __name__ == "__main__":
    asyncio.run(test_complete_workflow())
