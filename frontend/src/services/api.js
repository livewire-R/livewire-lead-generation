// API service for LEED.io Lead Generation Platform

class ApiService {
  constructor() {
    this.baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';
  }

  // Helper method to get auth token
  getToken() {
    return localStorage.getItem('authToken');
  }

  // Helper method to set auth token
  setToken(token) {
    localStorage.setItem('authToken', token);
  }

  // Helper method to remove auth token
  removeToken() {
    localStorage.removeItem('authToken');
  }

  // Authentication methods
  async login(email, password) {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, password })
    });
    
    const data = await response.json();
    
    if (data.success && data.token) {
      this.setToken(data.token);
    }
    
    return data;
  }

  async adminLogin(email, password) {
    const response = await fetch(`${this.baseURL}/auth/admin/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, password })
    });
    
    const data = await response.json();
    
    if (data.success && data.token) {
      this.setToken(data.token);
    }
    
    return data;
  }

  async register(userData) {
    const response = await fetch(`${this.baseURL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(userData)
    });
    
    return await response.json();
  }

  async logout() {
    this.removeToken();
    return { success: true };
  }

  // Health check
  async healthCheck() {
    const response = await fetch(`${this.baseURL}/health`);
    return await response.json();
  }

  // Create campaign from onboarding
  async createOnboardingCampaign(onboardingData) {
    const response = await fetch(`${this.baseURL}/onboarding/campaign`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getToken()}`
      },
      body: JSON.stringify(onboardingData)
    });
    
    return await response.json();
  }

  // Campaign management
  async getCampaigns() {
    const response = await fetch(`${this.baseURL}/campaigns`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${this.getToken()}`
      }
    });
    
    return await response.json();
  }

  async getCampaign(campaignId) {
    const response = await fetch(`${this.baseURL}/campaigns/${campaignId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${this.getToken()}`
      }
    });
    
    return await response.json();
  }

  async createCampaign(campaignData) {
    const response = await fetch(`${this.baseURL}/campaigns`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getToken()}`
      },
      body: JSON.stringify(campaignData)
    });
    
    return await response.json();
  }

  async updateCampaign(campaignId, campaignData) {
    const response = await fetch(`${this.baseURL}/campaigns/${campaignId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getToken()}`
      },
      body: JSON.stringify(campaignData)
    });
    
    return await response.json();
  }

  async deleteCampaign(campaignId) {
    const response = await fetch(`${this.baseURL}/campaigns/${campaignId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${this.getToken()}`
      }
    });
    
    return await response.json();
  }

  async pauseCampaign(campaignId) {
    const response = await fetch(`${this.baseURL}/campaigns/${campaignId}/pause`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.getToken()}`
      }
    });
    
    return await response.json();
  }

  async resumeCampaign(campaignId) {
    const response = await fetch(`${this.baseURL}/campaigns/${campaignId}/resume`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.getToken()}`
      }
    });
    
    return await response.json();
  }

  async runCampaignNow(campaignId) {
    const response = await fetch(`${this.baseURL}/campaigns/${campaignId}/run`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.getToken()}`
      }
    });
    
    return await response.json();
  }

  async getCampaignExecutions(campaignId, page = 1, perPage = 20) {
    const response = await fetch(`${this.baseURL}/campaigns/${campaignId}/executions?page=${page}&per_page=${perPage}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${this.getToken()}`
      }
    });
    
    return await response.json();
  }

  // Lead generation
  async generateLeads(criteria) {
    const response = await fetch(`${this.baseURL}/leads/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getToken()}`
      },
      body: JSON.stringify(criteria)
    });
    
    return await response.json();
  }

  async getLeads(page = 1, perPage = 20) {
    const response = await fetch(`${this.baseURL}/leads?page=${page}&per_page=${perPage}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${this.getToken()}`
      }
    });
    
    return await response.json();
  }

  async getLead(leadId) {
    const response = await fetch(`${this.baseURL}/leads/${leadId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${this.getToken()}`
      }
    });
    
    return await response.json();
  }

  // Client profile
  async getProfile() {
    const response = await fetch(`${this.baseURL}/auth/profile`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${this.getToken()}`
      }
    });
    
    return await response.json();
  }

  async updateProfile(profileData) {
    const response = await fetch(`${this.baseURL}/auth/profile`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getToken()}`
      },
      body: JSON.stringify(profileData)
    });
    
    return await response.json();
  }

  // Admin methods
  async getClients() {
    const response = await fetch(`${this.baseURL}/admin/clients`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${this.getToken()}`
      }
    });
    
    return await response.json();
  }

  async getSystemStats() {
    const response = await fetch(`${this.baseURL}/admin/stats`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${this.getToken()}`
      }
    });
    
    return await response.json();
  }
}

// Create and export a singleton instance
const apiService = new ApiService();
export default apiService;

