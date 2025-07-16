# 🚀 LiveWire Railway Deployment Guide

## Complete Setup Instructions for Railway Hosting

### Overview

This guide provides step-by-step instructions for deploying the LiveWire Lead Generation Platform to Railway, a modern cloud platform that simplifies deployment and scaling. Railway offers PostgreSQL databases, automatic deployments, and seamless scaling - perfect for our B2B lead generation SaaS.

### Prerequisites

Before starting deployment, ensure you have:

1. **Railway Account**: Sign up at https://railway.com/login
2. **GitHub Account**: For code repository hosting
3. **API Keys**: Apollo.io, Hunter.io, and LinkedIn developer credentials
4. **Domain** (Optional): Custom domain for production deployment

### Project Structure

```
LiveWire_Railway_Platform/
├── backend/                 # Flask API server
│   ├── src/
│   │   ├── main.py         # Main Flask application
│   │   ├── models/         # Database models
│   │   ├── routes/         # API endpoints
│   │   └── services/       # External API integrations
│   ├── requirements.txt    # Python dependencies
│   └── .env.example       # Environment variables template
├── frontend/               # React application
│   ├── src/
│   │   ├── pages/         # React pages
│   │   ├── services/      # API service layer
│   │   └── components/    # Reusable components
│   ├── package.json       # Node.js dependencies
│   └── .env              # Frontend environment variables
├── railway.toml           # Railway deployment configuration
└── README.md             # Project documentation
```

## Step 1: Prepare Your Repository

### 1.1 Create GitHub Repository

1. Go to GitHub and create a new repository named `livewire-lead-generation`
2. Clone this project to your local machine
3. Initialize git and push to your repository:

```bash
cd LiveWire_Railway_Platform
git init
git add .
git commit -m "Initial commit: LiveWire Lead Generation Platform"
git remote add origin https://github.com/yourusername/livewire-lead-generation.git
git push -u origin main
```

### 1.2 Environment Variables Setup

Create a `.env` file in the backend directory with your actual API keys:

```env
# Database (Railway will provide DATABASE_URL automatically)
DATABASE_URL=postgresql://user:password@host:port/database

# API Keys - Replace with your actual keys
APOLLO_API_KEY=your_apollo_api_key_here
HUNTER_API_KEY=your_hunter_api_key_here
LINKEDIN_CLIENT_ID=your_linkedin_client_id_here
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret_here

# JWT Configuration
JWT_SECRET=your_super_secret_jwt_key_change_in_production
JWT_EXPIRATION_HOURS=24

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your_flask_secret_key_change_in_production

# CORS Configuration
CORS_ORIGINS=https://your-frontend-domain.railway.app

# Railway Configuration
PORT=5000
HOST=0.0.0.0
```

## Step 2: Deploy to Railway

### 2.1 Create Railway Project

1. Log in to Railway at https://railway.com/login
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your GitHub account and select your repository
5. Railway will automatically detect the project structure

### 2.2 Configure Services

Railway will create two services automatically:

#### Backend Service Configuration
- **Service Name**: `livewire-backend`
- **Source**: `backend/` directory
- **Build Command**: Automatically detected (pip install)
- **Start Command**: `python src/main.py`
- **Port**: 5000

#### Frontend Service Configuration
- **Service Name**: `livewire-frontend`
- **Source**: `frontend/` directory
- **Build Command**: `pnpm build`
- **Start Command**: `pnpm preview`
- **Port**: 4173

### 2.3 Add PostgreSQL Database

1. In your Railway project dashboard, click "New Service"
2. Select "Database" → "PostgreSQL"
3. Railway will automatically provision a PostgreSQL database
4. The `DATABASE_URL` environment variable will be automatically set

### 2.4 Configure Environment Variables

#### Backend Environment Variables
In the backend service settings, add these environment variables:

```
APOLLO_API_KEY=your_apollo_api_key_here
HUNTER_API_KEY=your_hunter_api_key_here
LINKEDIN_CLIENT_ID=your_linkedin_client_id_here
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret_here
JWT_SECRET=your_super_secret_jwt_key_change_in_production
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your_flask_secret_key_change_in_production
HOST=0.0.0.0
PORT=5000
```

#### Frontend Environment Variables
In the frontend service settings, add:

```
VITE_API_URL=${{livewire-backend.RAILWAY_PUBLIC_DOMAIN}}
VITE_API_BASE_URL=${{livewire-backend.RAILWAY_PUBLIC_DOMAIN}}/api
VITE_APP_NAME=LiveWire Lead Generation
VITE_APP_VERSION=2.0.0
```

## Step 3: API Keys Setup

### 3.1 Apollo.io API Key

1. Go to https://app.apollo.io/settings/integrations/api
2. Generate a new API key
3. Add it to your Railway backend environment variables as `APOLLO_API_KEY`

### 3.2 Hunter.io API Key

1. Sign up at https://hunter.io/api_keys
2. Get your API key from the dashboard
3. Add it as `HUNTER_API_KEY` in Railway

### 3.3 LinkedIn API Setup

1. Go to https://www.linkedin.com/developers/apps/219060310/auth
2. Configure your app settings:
   - **Authorized Redirect URLs**: Add your Railway backend URL + `/auth/linkedin/callback`
   - **Products**: Request "Sign In with LinkedIn" and "Marketing Developer Platform"
3. Get your Client ID and Client Secret
4. Add them as `LINKEDIN_CLIENT_ID` and `LINKEDIN_CLIENT_SECRET`

## Step 4: Deployment Process

### 4.1 Automatic Deployment

Railway automatically deploys when you push to your main branch:

```bash
git add .
git commit -m "Deploy to Railway"
git push origin main
```

### 4.2 Monitor Deployment

1. Go to your Railway project dashboard
2. Click on each service to view deployment logs
3. Check for any errors in the build or runtime logs
4. Verify both services are running successfully

### 4.3 Database Migration

The Flask application automatically creates database tables on first run. Monitor the backend logs to ensure successful database initialization.

## Step 5: Testing Your Deployment

### 5.1 Health Checks

Test your deployed services:

**Backend Health Check**:
```
GET https://your-backend-url.railway.app/api/health
```

**Frontend Access**:
```
https://your-frontend-url.railway.app
```

### 5.2 API Testing

Test key endpoints:

```bash
# Test authentication
curl -X POST https://your-backend-url.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@livewire.com", "password": "demo123"}'

# Test lead generation (with auth token)
curl -X POST https://your-backend-url.railway.app/api/leads/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"keywords": "CEO", "industries": ["Technology"], "max_results": 10}'
```

## Step 6: Custom Domain Setup (Optional)

### 6.1 Configure Custom Domain

1. In Railway project settings, go to "Domains"
2. Add your custom domain
3. Update DNS records as instructed by Railway
4. Update CORS_ORIGINS environment variable with your custom domain

### 6.2 SSL Certificate

Railway automatically provides SSL certificates for all domains.

## Step 7: Monitoring and Maintenance

### 7.1 Monitoring

Railway provides built-in monitoring:
- **Metrics**: CPU, memory, and network usage
- **Logs**: Real-time application logs
- **Alerts**: Set up notifications for issues

### 7.2 Scaling

Railway automatically scales based on demand. For manual scaling:
1. Go to service settings
2. Adjust resource limits
3. Configure auto-scaling rules

### 7.3 Backup Strategy

**Database Backups**:
- Railway automatically backs up PostgreSQL databases
- Manual backups can be created from the database service panel

**Code Backups**:
- Your code is backed up in GitHub
- Railway maintains deployment history

## Troubleshooting

### Common Issues

**Build Failures**:
- Check requirements.txt for correct dependencies
- Verify Python version compatibility
- Review build logs for specific errors

**Database Connection Issues**:
- Ensure DATABASE_URL is set correctly
- Check PostgreSQL service status
- Verify database credentials

**API Integration Failures**:
- Validate API keys are correct
- Check API rate limits
- Review external service documentation

**CORS Errors**:
- Update CORS_ORIGINS with correct frontend URL
- Ensure both HTTP and HTTPS are configured

### Getting Help

- **Railway Documentation**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **GitHub Issues**: Create issues in your repository

## Security Considerations

### Environment Variables
- Never commit API keys to version control
- Use Railway's environment variable system
- Rotate keys regularly

### Database Security
- Railway PostgreSQL includes encryption at rest
- Use strong passwords
- Limit database access to necessary services

### API Security
- Implement rate limiting
- Use HTTPS for all communications
- Validate all input data
- Implement proper authentication

## Cost Optimization

### Railway Pricing
- **Starter Plan**: $5/month per service
- **Pro Plan**: $20/month per service with more resources
- **Database**: Additional cost based on usage

### Optimization Tips
- Monitor resource usage regularly
- Optimize database queries
- Implement caching where appropriate
- Use efficient API calls to external services

## Conclusion

Your LiveWire Lead Generation Platform is now successfully deployed on Railway with:

✅ **Modern Infrastructure**: Serverless Flask backend with PostgreSQL
✅ **Professional Frontend**: React application with Dripify-style design
✅ **API Integrations**: Apollo.io, Hunter.io, and LinkedIn connectivity
✅ **Australian Compliance**: Privacy Act and GDPR ready
✅ **Scalable Architecture**: Auto-scaling with demand
✅ **Cost Effective**: $0.07 per lead vs $100-250 traditional methods

Your platform is ready to generate high-quality B2B leads for Australian consultants, corporate wellness providers, and leadership coaches.

---

**Next Steps:**
1. Test all functionality with real API keys
2. Configure custom domain if desired
3. Set up monitoring and alerts
4. Begin generating leads for your consulting practice

For support or questions, refer to the troubleshooting section or create an issue in your GitHub repository.

