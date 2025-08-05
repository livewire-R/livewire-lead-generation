import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, Clock, Target, Building, MapPin, Users, CheckCircle, ArrowRight, ArrowLeft } from 'lucide-react';
import apiService from '../services/api';

const OnboardingPage = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [userProfile, setUserProfile] = useState(null);
  const [formData, setFormData] = useState({
    business_type: '',
    target_industries: [],
    target_locations: ['Australia'],
    target_titles: [],
    company_sizes: [],
    target_keywords: '',
    prospecting_frequency: '1x_day',
    preferred_time: '09:00',
    leads_per_run: 50,
    total_leads_limit: null,
    min_lead_score: 70
  });

  // Check authentication on component mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = apiService.getToken();
      if (!token) {
        navigate('/login', { 
          state: { 
            message: 'Please log in to access the onboarding process.' 
          }
        });
        return;
      }

      try {
        // Get user profile to personalize onboarding
        const profileResponse = await apiService.getProfile();
        if (profileResponse.success) {
          setUserProfile(profileResponse.client);
        }
      } catch (error) {
        console.error('Failed to load user profile:', error);
        // Continue with onboarding even if profile fails
      }
    };

    checkAuth();
  }, [navigate]);

  const businessTypes = [
    { id: 'consultant', label: 'Business Consultant', icon: Building },
    { id: 'leadership_coach', label: 'Leadership Coach', icon: Users },
    { id: 'wellness', label: 'Corporate Wellness', icon: Target },
    { id: 'hr_consultant', label: 'HR Consultant', icon: Users },
    { id: 'it_consultant', label: 'IT Consultant', icon: Building },
    { id: 'other', label: 'Other', icon: Building }
  ];

  const industries = [
    'Technology', 'Healthcare', 'Finance', 'Manufacturing', 'Retail',
    'Education', 'Real Estate', 'Construction', 'Professional Services',
    'Government', 'Non-profit', 'Energy', 'Transportation', 'Media'
  ];

  const companySizes = [
    { id: '1-10', label: '1-10 employees' },
    { id: '11-50', label: '11-50 employees' },
    { id: '51-200', label: '51-200 employees' },
    { id: '201-500', label: '201-500 employees' },
    { id: '501-1000', label: '501-1000 employees' },
    { id: '1000+', label: '1000+ employees' }
  ];

  const jobTitles = [
    'CEO', 'CTO', 'CFO', 'COO', 'VP', 'Director', 'Manager',
    'Head of', 'Chief', 'President', 'Owner', 'Founder'
  ];

  const frequencyOptions = [
    { id: '1x_day', label: '1x per day', description: 'Daily lead generation at your preferred time' },
    { id: '2x_day', label: '2x per day', description: 'Morning and afternoon lead generation' },
    { id: '3x_week', label: '3x per week', description: 'Monday, Wednesday, Friday lead generation' },
    { id: '1x_week', label: '1x per week', description: 'Weekly lead generation on your chosen day' },
    { id: '2x_month', label: '2x per month', description: 'Bi-monthly lead generation' },
    { id: '1x_month', label: '1x per month', description: 'Monthly lead generation' }
  ];

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleArrayToggle = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].includes(value)
        ? prev[field].filter(item => item !== value)
        : [...prev[field], value]
    }));
  };

  const nextStep = () => {
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      // Double-check authentication
      const token = apiService.getToken();
      if (!token) {
        navigate('/login', { 
          state: { 
            message: 'Your session has expired. Please log in again.' 
          }
        });
        return;
      }

      // Create campaign for authenticated user
      const campaignData = {
        name: `${businessTypes.find(t => t.id === formData.business_type)?.label || 'Lead Generation'} Campaign`,
        description: `Automated lead generation campaign for ${formData.target_industries.join(', ')} industries`,
        criteria: {
          industries: formData.target_industries,
          job_titles: formData.target_titles,
          company_sizes: formData.company_sizes,
          keywords: formData.target_keywords,
          locations: formData.target_locations
        },
        frequency: formData.prospecting_frequency,
        preferred_time: formData.preferred_time,
        max_leads_per_run: formData.leads_per_run,
        max_leads_total: formData.total_leads_limit,
        min_lead_score: formData.min_lead_score
      };

      console.log('Creating campaign with data:', campaignData);
      
      const response = await apiService.createCampaign(campaignData);
      
      if (response.success) {
        navigate('/dashboard', { 
          state: { 
            message: `Welcome ${userProfile?.contact_name || 'to LEED.io'}! Your lead generation campaign has been set up successfully.`,
            campaignId: response.campaign.id,
            isNewCampaign: true
          }
        });
      } else {
        throw new Error(response.error || 'Failed to create campaign');
      }
      
    } catch (error) {
      console.error('Campaign creation error:', error);
      alert(`Failed to create campaign: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">What type of business are you in?</h2>
        <p className="text-gray-600">This helps us optimize lead generation for your industry</p>
        {userProfile && (
          <p className="text-sm text-blue-600 mt-2">
            Setting up campaign for {userProfile.company_name}
          </p>
        )}
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {businessTypes.map((type) => {
          const Icon = type.icon;
          return (
            <button
              key={type.id}
              onClick={() => handleInputChange('business_type', type.id)}
              className={`p-4 rounded-lg border-2 transition-all ${
                formData.business_type === type.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center space-x-3">
                <Icon className="h-6 w-6 text-blue-600" />
                <span className="font-medium text-gray-900">{type.label}</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Define your ideal prospects</h2>
        <p className="text-gray-600">Help us find the right leads for your business</p>
      </div>
      
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Target Industries</label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {industries.map((industry) => (
              <button
                key={industry}
                onClick={() => handleArrayToggle('target_industries', industry)}
                className={`p-2 text-sm rounded-md border transition-all ${
                  formData.target_industries.includes(industry)
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                {industry}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Job Titles</label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {jobTitles.map((title) => (
              <button
                key={title}
                onClick={() => handleArrayToggle('target_titles', title)}
                className={`p-2 text-sm rounded-md border transition-all ${
                  formData.target_titles.includes(title)
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                {title}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Company Sizes</label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {companySizes.map((size) => (
              <button
                key={size.id}
                onClick={() => handleArrayToggle('company_sizes', size.id)}
                className={`p-2 text-sm rounded-md border transition-all ${
                  formData.company_sizes.includes(size.id)
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                {size.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Keywords (Optional)</label>
          <input
            type="text"
            value={formData.target_keywords}
            onChange={(e) => handleInputChange('target_keywords', e.target.value)}
            placeholder="e.g., digital transformation, leadership development"
            className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="text-sm text-gray-500 mt-1">Additional keywords to help find relevant prospects</p>
        </div>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">How often would you like to prospect?</h2>
        <p className="text-gray-600">Set up automated lead generation that works for your schedule</p>
      </div>
      
      <div className="space-y-4">
        {frequencyOptions.map((option) => (
          <button
            key={option.id}
            onClick={() => handleInputChange('prospecting_frequency', option.id)}
            className={`w-full p-4 rounded-lg border-2 text-left transition-all ${
              formData.prospecting_frequency === option.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-900">{option.label}</div>
                <div className="text-sm text-gray-600">{option.description}</div>
              </div>
              {formData.prospecting_frequency === option.id && (
                <CheckCircle className="h-5 w-5 text-blue-600" />
              )}
            </div>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Preferred Time</label>
          <input
            type="time"
            value={formData.preferred_time}
            onChange={(e) => handleInputChange('preferred_time', e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Leads per Run</label>
          <select
            value={formData.leads_per_run}
            onChange={(e) => handleInputChange('leads_per_run', parseInt(e.target.value))}
            className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value={25}>25 leads</option>
            <option value={50}>50 leads</option>
            <option value={100}>100 leads</option>
            <option value={200}>200 leads</option>
          </select>
        </div>
      </div>
    </div>
  );

  const renderStep4 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Review your setup</h2>
        <p className="text-gray-600">Confirm your automated lead generation settings</p>
      </div>
      
      <div className="bg-gray-50 rounded-lg p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h3 className="font-medium text-gray-900 mb-2">Business Type</h3>
            <p className="text-gray-600">
              {businessTypes.find(t => t.id === formData.business_type)?.label || 'Not selected'}
            </p>
          </div>
          
          <div>
            <h3 className="font-medium text-gray-900 mb-2">Prospecting Frequency</h3>
            <p className="text-gray-600">
              {frequencyOptions.find(f => f.id === formData.prospecting_frequency)?.label || 'Not selected'}
            </p>
          </div>
          
          <div>
            <h3 className="font-medium text-gray-900 mb-2">Preferred Time</h3>
            <p className="text-gray-600">{formData.preferred_time} AEST</p>
          </div>
          
          <div>
            <h3 className="font-medium text-gray-900 mb-2">Leads per Run</h3>
            <p className="text-gray-600">{formData.leads_per_run} leads</p>
          </div>
        </div>
        
        <div>
          <h3 className="font-medium text-gray-900 mb-2">Target Industries</h3>
          <div className="flex flex-wrap gap-2">
            {formData.target_industries.map((industry) => (
              <span key={industry} className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded">
                {industry}
              </span>
            ))}
          </div>
        </div>
        
        <div>
          <h3 className="font-medium text-gray-900 mb-2">Target Job Titles</h3>
          <div className="flex flex-wrap gap-2">
            {formData.target_titles.map((title) => (
              <span key={title} className="px-2 py-1 bg-green-100 text-green-800 text-sm rounded">
                {title}
              </span>
            ))}
          </div>
        </div>
      </div>
      
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <Clock className="h-5 w-5 text-blue-600 mt-0.5" />
          <div>
            <h4 className="font-medium text-blue-900">Automated Lead Generation</h4>
            <p className="text-sm text-blue-700 mt-1">
              Your campaign will automatically generate leads according to your schedule. 
              You can pause, modify, or stop the campaign at any time from your dashboard.
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  const isStepValid = () => {
    switch (currentStep) {
      case 1:
        return formData.business_type !== '';
      case 2:
        return formData.target_industries.length > 0 && formData.target_titles.length > 0;
      case 3:
        return formData.prospecting_frequency !== '';
      case 4:
        return true;
      default:
        return false;
    }
  };

  // Show loading if checking authentication
  if (!userProfile && !apiService.getToken()) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Checking authentication...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-2 rounded-lg">
              <Zap className="h-6 w-6 text-white" />
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              LEED.io
            </span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome to LEED.io</h1>
          <p className="text-gray-600">Let's set up your automated lead generation campaign</p>
          {userProfile && (
            <p className="text-sm text-blue-600 mt-2">
              Logged in as {userProfile.contact_name} ({userProfile.company_name})
            </p>
          )}
        </div>

        {/* Progress Bar */}
        <div className="max-w-2xl mx-auto mb-8">
          <div className="flex items-center justify-between">
            {[1, 2, 3, 4].map((step) => (
              <div key={step} className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step <= currentStep
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-600'
                }`}>
                  {step}
                </div>
                {step < 4 && (
                  <div className={`w-16 h-1 mx-2 ${
                    step < currentStep ? 'bg-blue-600' : 'bg-gray-200'
                  }`} />
                )}
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-2 text-xs text-gray-600">
            <span>Business</span>
            <span>Prospects</span>
            <span>Schedule</span>
            <span>Review</span>
          </div>
        </div>

        {/* Step Content */}
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-lg p-8">
            {currentStep === 1 && renderStep1()}
            {currentStep === 2 && renderStep2()}
            {currentStep === 3 && renderStep3()}
            {currentStep === 4 && renderStep4()}
          </div>

          {/* Navigation */}
          <div className="flex justify-between mt-6">
            <button
              onClick={prevStep}
              disabled={currentStep === 1}
              className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-medium transition-all ${
                currentStep === 1
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Previous</span>
            </button>

            {currentStep < 4 ? (
              <button
                onClick={nextStep}
                disabled={!isStepValid()}
                className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-medium transition-all ${
                  isStepValid()
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                }`}
              >
                <span>Next</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={loading || !isStepValid()}
                className={`flex items-center space-x-2 px-8 py-3 rounded-lg font-medium transition-all ${
                  loading || !isStepValid()
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700'
                }`}
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Creating Campaign...</span>
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4" />
                    <span>Start Lead Generation</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OnboardingPage;

