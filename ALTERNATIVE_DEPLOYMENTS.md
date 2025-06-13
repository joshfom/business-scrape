# Alternative Deployment Options for Business Scraper

In addition to deploying on a VPS as described in the main DEPLOYMENT_GUIDE.md, here are other deployment options for your Business Scraper application.

## Option 1: Deploying on AWS Elastic Beanstalk

AWS Elastic Beanstalk provides an easy way to deploy and scale web applications with minimal configuration.

### Prerequisites
- AWS account
- AWS CLI installed and configured
- EB CLI installed (`pip install awsebcli`)

### Steps

1. **Initialize EB CLI in your project**:
   ```bash
   cd /path/to/business-scrape
   eb init
   ```
   Follow the prompts to select your region and create a new application.

2. **Create a Procfile**:
   ```bash
   # Procfile
   web: cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

3. **Create an .ebextensions folder** with MongoDB setup:
   ```bash
   mkdir -p .ebextensions
   ```

   Create a file `.ebextensions/01_mongo.config`:
   ```yaml
   packages:
     yum:
       mongodb-org-server: []
   
   commands:
     01_create_mongo_service:
       command: "echo '[mongodb-org-4.4]
   name=MongoDB Repository
   baseurl=https://repo.mongodb.org/yum/amazon/2/mongodb-org/4.4/x86_64/
   gpgcheck=1
   enabled=1
   gpgkey=https://www.mongodb.org/static/pgp/server-4.4.asc' > /etc/yum.repos.d/mongodb-org-4.4.repo"
   
   services:
     sysvinit:
       mongod:
         enabled: true
         ensureRunning: true
   ```

4. **Deploy to Elastic Beanstalk**:
   ```bash
   eb create business-scraper-env
   ```

5. **Configure environment variables**:
   In the AWS Console, go to your Elastic Beanstalk application, navigate to Configuration > Software, and add the necessary environment variables.

## Option 2: Deploying with Docker

Docker allows you to package your application with all dependencies in a container.

### Prerequisites
- Docker installed
- Docker Compose installed

### Steps

1. **Create a Dockerfile for the backend**:
   ```Dockerfile
   FROM python:3.9
   
   WORKDIR /app
   
   COPY backend/requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY backend/ .
   
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **Create a Dockerfile for the frontend**:
   ```Dockerfile
   FROM node:14 as build
   
   WORKDIR /app
   
   COPY frontend/package*.json ./
   RUN npm install
   
   COPY frontend/ ./
   RUN npm run build
   
   FROM nginx:stable-alpine
   COPY --from=build /app/build /usr/share/nginx/html
   COPY nginx.conf /etc/nginx/conf.d/default.conf
   
   EXPOSE 80
   
   CMD ["nginx", "-g", "daemon off;"]
   ```

3. **Create an NGINX configuration file** (`nginx.conf`):
   ```nginx
   server {
       listen 80;
       
       location / {
           root /usr/share/nginx/html;
           index index.html;
           try_files $uri $uri/ /index.html;
       }
       
       location /api {
           proxy_pass http://backend:8000/api;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

4. **Create a docker-compose.yml file**:
   ```yaml
   version: '3'
   
   services:
     mongodb:
       image: mongo:4.4
       ports:
         - "27017:27017"
       volumes:
         - mongodb_data:/data/db
       restart: always
   
     backend:
       build:
         context: .
         dockerfile: Dockerfile.backend
       ports:
         - "8000:8000"
       depends_on:
         - mongodb
       environment:
         - MONGODB_URI=mongodb://mongodb:27017/business_scraper
       restart: always
   
     frontend:
       build:
         context: .
         dockerfile: Dockerfile.frontend
       ports:
         - "80:80"
       depends_on:
         - backend
       restart: always
   
   volumes:
     mongodb_data:
   ```

5. **Build and run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

## Option 3: Deploying on Render

Render is a cloud provider that offers free hosting for web services, static sites, and databases.

### Steps

1. **Push your code to GitHub or GitLab**.

2. **Create a render.yaml file**:
   ```yaml
   services:
     - name: business-scraper-backend
       type: web
       env: python
       buildCommand: cd backend && pip install -r requirements.txt
       startCommand: cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT
       envVars:
         - key: MONGODB_URI
           fromDatabase:
             name: business-scraper-db
             property: connectionString
   
     - name: business-scraper-frontend
       type: web
       env: static
       buildCommand: cd frontend && npm install && npm run build
       staticPublishPath: ./frontend/build
       routes:
         - type: rewrite
           source: /api/*
           destination: https://business-scraper-backend.onrender.com/api/*
   
   databases:
     - name: business-scraper-db
       type: mongo
       ipAllowList: []  # Only allow internal connections
   ```

3. **Sign up for Render** and connect your repository.

4. **Deploy from the Dashboard** by selecting "Blueprint" and choosing your repository.

## Option 4: Deploying on Heroku

Although Heroku no longer offers a free tier, it's still a straightforward platform for deployment.

### Prerequisites
- Heroku account
- Heroku CLI installed

### Steps

1. **Login to Heroku**:
   ```bash
   heroku login
   ```

2. **Create a Heroku app**:
   ```bash
   heroku create business-scraper
   ```

3. **Add MongoDB add-on**:
   ```bash
   heroku addons:create mongolab:sandbox
   ```

4. **Create a Procfile**:
   ```
   web: cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

5. **Set up environment variables**:
   ```bash
   heroku config:set REACT_APP_API_URL=https://your-app-name.herokuapp.com/api
   ```

6. **Deploy to Heroku**:
   ```bash
   git push heroku main
   ```

## Conclusion

Choose the deployment option that best fits your needs:

1. **VPS (see DEPLOYMENT_GUIDE.md)**: Full control, potentially cheaper for long-term use
2. **AWS Elastic Beanstalk**: Managed service with good scalability
3. **Docker**: Consistent deployments across environments
4. **Render**: Simple cloud deployment with free tier
5. **Heroku**: Easy deployment but paid-only

Each option has trade-offs regarding cost, complexity, and scalability. For a small to medium scraper application, a VPS is often the most cost-effective solution with good performance.
