// MongoDB initialization script
// This runs when the database is first created

// Create the business_scraper database
db = db.getSiblingDB('business_scraper');

// Create collections with indexes for better performance
db.createCollection('businesses');
db.createCollection('scraping_jobs');
db.createCollection('scraping_progress');

// Create indexes for better query performance
db.businesses.createIndex({ "page_url": 1 }, { unique: true });
db.businesses.createIndex({ "name": 1 });
db.businesses.createIndex({ "city": 1 });
db.businesses.createIndex({ "created_at": 1 });

db.scraping_jobs.createIndex({ "status": 1 });
db.scraping_jobs.createIndex({ "created_at": 1 });
db.scraping_jobs.createIndex({ "domains": 1 });

db.scraping_progress.createIndex({ "job_id": 1 });
db.scraping_progress.createIndex({ "timestamp": 1 });
db.scraping_progress.createIndex({ "job_id": 1, "timestamp": 1 });

print('✅ Business Scraper database initialized with indexes');
