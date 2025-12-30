import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Home, LayoutDashboard, Bookmark, Edit2, Trash2, ChevronDown, ChevronUp, User, ArrowLeft, ExternalLink, Calendar, MapPin, Briefcase, DollarSign, TrendingUp, Clock, Star, Edit3, Save } from 'lucide-react';

export default function JobTrackerApp() {
  const [isNavExpanded, setIsNavExpanded] = useState(true);
  const [currentPage, setCurrentPage] = useState('saved-jobs');
  const [selectedJob, setSelectedJob] = useState(null);
  const [sortField, setSortField] = useState(null);
  const [sortDirection, setSortDirection] = useState('asc');
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [isEditingNotes, setIsEditingNotes] = useState(false);
  const [isDescriptionExpanded, setIsDescriptionExpanded] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false); // Track login status
  
  const [jobs, setJobs] = useState([
    { 
      id: 1, 
      job_title: 'Full Stack Engineer', 
      company_name: 'Innovate Labs',
      job_description: 'We are seeking a talented Full Stack Engineer to join our dynamic team. You will be responsible for developing and maintaining web applications using modern technologies. This role offers the opportunity to work on cutting-edge projects and collaborate with a passionate team of developers.\n\nKey Responsibilities:\n• Design and implement scalable web applications\n• Collaborate with cross-functional teams\n• Write clean, maintainable code\n• Participate in code reviews and mentor junior developers\n• Stay current with emerging technologies\n\nQualifications:\n• 5+ years of experience in full-stack development\n• Strong proficiency in React, Node.js, and TypeScript\n• Experience with cloud platforms (AWS, Azure, or GCP)\n• Excellent problem-solving and communication skills\n• Bachelor\'s degree in Computer Science or related field',
      salary_range: '$120k - $140k', 
      location: 'San Francisco, CA',
      remote_type: 'hybrid',
      role_type: 'full_time',
      experience_level: 'senior',
      interest_level: 'high',
      application_status: 'applied', 
      application_date: '2024-11-12',
      job_fit_score: 'strong',
      job_fit_reason: 'Your extensive experience with React and Node.js aligns perfectly with the role requirements. The senior-level position matches your 7+ years of experience, and your AWS certifications make you a strong candidate for their cloud-based architecture.',
      notes: 'Remote position - spoke with recruiter, technical interview scheduled for next week. Team seems great, good culture fit. Need to prepare system design questions.',
      targeted_resume_url: 'https://drive.google.com/file/d/abc123/view',
      targeted_cover_letter_url: 'https://drive.google.com/file/d/xyz789/view'
    },
    { 
      id: 2, 
      job_title: 'Lead Designer', 
      company_name: 'Design Studio',
      job_description: 'Looking for an experienced Lead Designer to guide our design team and create exceptional user experiences. You will work closely with product managers and engineers to bring innovative designs to life.\n\nResponsibilities:\n• Lead design projects from concept to delivery\n• Mentor junior designers\n• Create design systems and style guides\n• Collaborate with stakeholders\n• Present design solutions to leadership',
      salary_range: '$110k - $130k', 
      location: 'New York, NY',
      remote_type: 'onsite',
      role_type: 'full_time',
      experience_level: 'lead',
      interest_level: 'medium',
      application_status: 'interviewing', 
      application_date: '2024-11-16',
      job_fit_score: 'good',
      job_fit_reason: 'Your portfolio demonstrates strong design leadership and your experience with design systems is valuable. However, the onsite requirement may be a consideration.',
      notes: 'Second interview scheduled - portfolio review went well',
      targeted_resume_url: 'https://drive.google.com/file/d/def456/view',
      targeted_cover_letter_url: 'https://drive.google.com/file/d/ghi789/view'
    },
    { 
      id: 3, 
      job_title: 'Data Analyst', 
      company_name: 'DataTech Solutions',
      job_description: 'Join our data team to analyze complex datasets and provide actionable insights. You will work with stakeholders across the organization to drive data-informed decision making.\n\nWhat you\'ll do:\n• Analyze large datasets using SQL and Python\n• Create dashboards and visualizations\n• Present findings to stakeholders\n• Develop predictive models',
      salary_range: '$90k - $105k', 
      location: 'Austin, TX',
      remote_type: 'remote',
      role_type: 'full_time',
      experience_level: 'mid',
      interest_level: 'medium',
      application_status: 'applied', 
      application_date: '2024-11-19',
      job_fit_score: 'fair',
      job_fit_reason: 'You have solid analytics skills, but the role requires more advanced statistical modeling experience than currently in your background.',
      notes: 'Referred by John - waiting for response',
      targeted_resume_url: 'https://drive.google.com/file/d/jkl012/view',
      targeted_cover_letter_url: 'https://drive.google.com/file/d/mno345/view'
    },
    { 
      id: 4, 
      job_title: 'DevOps Engineer', 
      company_name: 'Cloud Systems',
      job_description: 'We need a skilled DevOps Engineer to manage our cloud infrastructure and streamline our deployment processes. Experience with AWS, Docker, and Kubernetes required.\n\nKey areas:\n• Manage AWS infrastructure\n• Implement CI/CD pipelines\n• Monitor system performance\n• Automate deployment processes\n• Ensure security best practices',
      salary_range: '$115k - $135k', 
      location: 'Seattle, WA',
      remote_type: 'hybrid',
      role_type: 'full_time',
      experience_level: 'senior',
      interest_level: 'high',
      application_status: 'offer', 
      application_date: '2024-11-21',
      job_fit_score: 'very_strong',
      job_fit_reason: 'Excellent match! Your DevOps expertise with AWS, Docker, and Kubernetes directly aligns with their tech stack. Your experience scaling infrastructure at previous companies is exactly what they need.',
      notes: 'Deadline: Nov 30 - excellent benefits package',
      targeted_resume_url: 'https://drive.google.com/file/d/pqr678/view',
      targeted_cover_letter_url: 'https://drive.google.com/file/d/stu901/view'
    },
  ]);

  const handleChange = (id, field, value) => {
    setJobs(jobs.map(job => job.id === id ? { ...job, [field]: value } : job));
    if (selectedJob && selectedJob.id === id) {
      setSelectedJob({ ...selectedJob, [field]: value });
    }
  };

  const handleDelete = (id) => {
    if (confirm('Are you sure you want to delete this job?')) {
      setJobs(jobs.filter(job => job.id !== id));
      if (selectedJob && selectedJob.id === id) {
        setSelectedJob(null);
      }
    }
  };

  const handleSort = (field) => {
    const newDirection = sortField === field && sortDirection === 'asc' ? 'desc' : 'asc';
    setSortField(field);
    setSortDirection(newDirection);
  };

  const sortedJobs = [...jobs].sort((a, b) => {
    if (!sortField) return 0;
    
    let aVal = a[sortField];
    let bVal = b[sortField];
    
    if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
    return 0;
  });

  const SortIcon = ({ field }) => {
    if (sortField !== field) return <ChevronDown size={14} className="opacity-30" />;
    return sortDirection === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />;
  };

  const getStatusColor = (status) => {
    const colors = {
      'saved': 'bg-blue-50 text-blue-600',
      'applied': 'bg-blue-100 text-blue-700',
      'interviewing': 'bg-blue-200 text-blue-800',
      'offer': 'bg-blue-300 text-blue-900',
      'rejected': 'bg-slate-100 text-slate-600'
    };
    return colors[status] || 'bg-slate-100 text-slate-700';
  };

  const getStatusColorDetailed = (status) => {
    const colors = {
      'saved': 'bg-blue-50 text-blue-600 border-blue-200',
      'applied': 'bg-blue-100 text-blue-700 border-blue-300',
      'interviewing': 'bg-blue-200 text-blue-800 border-blue-400',
      'offer': 'bg-blue-300 text-blue-900 border-blue-500',
      'rejected': 'bg-slate-100 text-slate-600 border-slate-300'
    };
    return colors[status] || 'bg-slate-100 text-slate-700 border-slate-300';
  };

  const getInterestColor = (level) => {
    const colors = {
      'high': 'bg-blue-300 text-blue-900',
      'medium': 'bg-blue-200 text-blue-800',
      'low': 'bg-blue-100 text-blue-700'
    };
    return colors[level] || 'bg-slate-100 text-slate-700';
  };

  const getFitColor = (score) => {
    const colors = {
      'very_strong': 'bg-blue-400 text-blue-950',
      'strong': 'bg-blue-300 text-blue-900',
      'good': 'bg-blue-200 text-blue-800',
      'fair': 'bg-blue-100 text-blue-700',
      'weak': 'bg-blue-50 text-blue-600'
    };
    return colors[score] || 'bg-slate-100 text-slate-700';
  };

  const formatLabel = (str) => {
    return str?.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  // Home Page View
  if (currentPage === 'home') {
    return (
      <div className="flex h-screen bg-slate-50">
        {/* Sidebar */}
        <div className={`${isNavExpanded ? 'w-72' : 'w-20'} bg-slate-900 text-slate-100 transition-all duration-300 flex flex-col shadow-xl`}>
          <div className="p-6 border-b border-slate-700">
            {isNavExpanded && (
              <div>
                <h1 className="text-2xl font-bold text-blue-400">Career Hub</h1>
                <p className="text-sm text-slate-400 mt-1">Track your applications</p>
              </div>
            )}
          </div>
          
          <nav className="flex-1 p-4 space-y-2">
            <button onClick={() => setCurrentPage('home')} className={`w-full flex items-center gap-4 p-4 rounded-lg transition ${currentPage === 'home' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800'}`}>
              <Home size={22} />
              {isNavExpanded && <span className="font-medium">Home</span>}
            </button>
            <button onClick={() => setCurrentPage('dashboard')} className={`w-full flex items-center gap-4 p-4 rounded-lg transition ${currentPage === 'dashboard' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800'}`}>
              <LayoutDashboard size={22} />
              {isNavExpanded && <span className="font-medium">Dashboard</span>}
            </button>
            <button onClick={() => setCurrentPage('saved-jobs')} className={`w-full flex items-center gap-4 p-4 rounded-lg transition ${currentPage === 'saved-jobs' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800'}`}>
              <Bookmark size={22} />
              {isNavExpanded && <span className="font-medium">Saved Jobs</span>}
            </button>
          </nav>

          <button onClick={() => setIsNavExpanded(!isNavExpanded)} className="p-4 border-t border-slate-700 hover:bg-slate-800 flex items-center justify-center">
            {isNavExpanded ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
          </button>
        </div>

        {/* Home Page Content */}
        <div className="flex-1 overflow-auto">
          {/* Top Bar */}
          <div className="bg-slate-900 text-slate-100 px-8 py-4 border-b border-slate-800">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                  <Star className="text-white" size={24} />
                </div>
                <div>
                  <h1 className="text-xl font-bold">Career Attendant</h1>
                  <p className="text-xs text-slate-400">Your AI-Powered Job Search Assistant</p>
                </div>
              </div>
              {isLoggedIn ? (
                <div className="relative">
                  <button 
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="p-2 bg-slate-800 rounded-lg hover:bg-slate-700 transition"
                  >
                    <User size={20} />
                  </button>
                  {showUserMenu && (
                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-slate-200 py-2 z-10">
                      <button className="w-full text-left px-4 py-2 hover:bg-slate-50 text-slate-700">Profile</button>
                      <button className="w-full text-left px-4 py-2 hover:bg-slate-50 text-slate-700">Account</button>
                      <button className="w-full text-left px-4 py-2 hover:bg-slate-50 text-slate-700">Settings</button>
                      <div className="border-t border-slate-200 my-1"></div>
                      <button 
                        onClick={() => setIsLoggedIn(false)}
                        className="w-full text-left px-4 py-2 hover:bg-slate-50 text-red-600"
                      >
                        Logout
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <button 
                  onClick={() => setIsLoggedIn(true)}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium text-sm"
                >
                  Login / Sign Up
                </button>
              )}
            </div>
          </div>

          {/* Hero Section */}
          <div className="relative bg-gradient-to-br from-slate-900 via-slate-800 to-blue-900 text-white overflow-hidden">
            <div className="absolute inset-0 opacity-10">
              <div className="absolute top-20 left-20 w-72 h-72 bg-blue-500 rounded-full blur-3xl"></div>
              <div className="absolute bottom-20 right-20 w-96 h-96 bg-purple-500 rounded-full blur-3xl"></div>
            </div>
            
            <div className="relative max-w-7xl mx-auto px-8 py-20">
              <div className="grid grid-cols-2 gap-16 items-center">
                <div>
                  <h2 className="text-6xl font-bold mb-6 leading-tight">
                    Transform Your Job Search with AI
                  </h2>
                  <p className="text-xl text-slate-300 mb-8 leading-relaxed">
                    Career Attendant streamlines your job hunt with intelligent tracking, AI-powered resume generation, and personalized job fit analysis. Land your dream role faster.
                  </p>
                  <div className="flex gap-4">
                    <button 
                      onClick={() => setCurrentPage('saved-jobs')}
                      className="px-8 py-4 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition font-semibold text-lg shadow-lg hover:shadow-xl"
                    >
                      View Your Jobs
                    </button>
                    <button className="px-8 py-4 bg-white/10 backdrop-blur-sm text-white rounded-xl hover:bg-white/20 transition font-semibold text-lg border border-white/20">
                      Learn More
                    </button>
                  </div>
                </div>

                <div className="relative">
                  <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border border-white/20 shadow-2xl">
                    <div className="space-y-4">
                      <div className="flex items-center gap-4 p-4 bg-white/10 rounded-xl">
                        <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
                          <TrendingUp size={24} />
                        </div>
                        <div className="flex-1">
                          <p className="font-semibold text-lg">Smart Job Matching</p>
                          <p className="text-sm text-slate-300">AI analyzes your fit for each role</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 p-4 bg-white/10 rounded-xl">
                        <div className="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
                          <Edit3 size={24} />
                        </div>
                        <div className="flex-1">
                          <p className="font-semibold text-lg">Tailored Documents</p>
                          <p className="text-sm text-slate-300">Auto-generate targeted resumes</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 p-4 bg-white/10 rounded-xl">
                        <div className="w-12 h-12 bg-emerald-600 rounded-lg flex items-center justify-center flex-shrink-0">
                          <Calendar size={24} />
                        </div>
                        <div className="flex-1">
                          <p className="font-semibold text-lg">Track Everything</p>
                          <p className="text-sm text-slate-300">Never miss a follow-up or deadline</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Stats Section */}
          <div className="bg-white border-b border-slate-200">
            <div className="max-w-7xl mx-auto px-8 py-16">
              <div className="grid grid-cols-4 gap-8">
                <div className="text-center">
                  <p className="text-5xl font-bold text-blue-600 mb-2">{jobs.length}</p>
                  <p className="text-slate-600 font-medium">Jobs Tracked</p>
                </div>
                <div className="text-center">
                  <p className="text-5xl font-bold text-blue-600 mb-2">{jobs.filter(j => j.application_status === 'interviewing' || j.application_status === 'offer').length}</p>
                  <p className="text-slate-600 font-medium">Active Opportunities</p>
                </div>
                <div className="text-center">
                  <p className="text-5xl font-bold text-blue-600 mb-2">{jobs.filter(j => j.interest_level === 'high').length}</p>
                  <p className="text-slate-600 font-medium">High Priority</p>
                </div>
                <div className="text-center">
                  <p className="text-5xl font-bold text-blue-600 mb-2">100%</p>
                  <p className="text-slate-600 font-medium">AI-Powered</p>
                </div>
              </div>
            </div>
          </div>

          {/* Job Aggregation Section */}
          <div className="bg-gradient-to-br from-slate-50 to-blue-50 border-b border-slate-200">
            <div className="max-w-7xl mx-auto px-8 py-20">
              <div className="text-center mb-12">
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-700 rounded-full font-semibold text-sm mb-6">
                  <Star size={16} className="fill-current" />
                  Unified Job Search
                </div>
                <h2 className="text-5xl font-bold text-slate-900 mb-6">One Dashboard. Every Job Board.</h2>
                <p className="text-xl text-slate-600 max-w-3xl mx-auto">
                  Aggregate opportunities from all major job boards and company career sites into a single, AI-powered interface. No more juggling multiple tabs and losing track of applications.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-12 items-center mb-16">
                <div>
                  <h3 className="text-3xl font-bold text-slate-900 mb-6">Search Once, Find Everywhere</h3>
                  <div className="space-y-4">
                    <div className="flex items-start gap-4">
                      <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <div>
                        <h4 className="text-lg font-semibold text-slate-900 mb-1">Major Job Boards</h4>
                        <p className="text-slate-600">LinkedIn, Indeed, Glassdoor, ZipRecruiter, and more</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-4">
                      <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <div>
                        <h4 className="text-lg font-semibold text-slate-900 mb-1">Company Career Pages</h4>
                        <p className="text-slate-600">Direct access to positions from company websites</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-4">
                      <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <div>
                        <h4 className="text-lg font-semibold text-slate-900 mb-1">Niche Industry Boards</h4>
                        <p className="text-slate-600">Tech, healthcare, finance, and specialized platforms</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-4">
                      <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
                        <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <div>
                        <h4 className="text-lg font-semibold text-slate-900 mb-1">Real-Time Syncing</h4>
                        <p className="text-slate-600">Automatic updates when new positions are posted</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="relative">
                  <div className="bg-white rounded-2xl shadow-xl p-8 border border-slate-200">
                    <div className="text-center mb-6">
                      <div className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold mb-2">
                        <Star size={16} className="fill-current" />
                        AI-Powered Aggregation
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-4 mb-6">
                      <div className="bg-blue-50 rounded-xl p-4 text-center border border-blue-100">
                        <div className="w-10 h-10 bg-blue-600 rounded-lg mx-auto mb-2 flex items-center justify-center">
                          <span className="text-white font-bold text-sm">Li</span>
                        </div>
                        <p className="text-xs font-medium text-slate-700">LinkedIn</p>
                      </div>
                      <div className="bg-green-50 rounded-xl p-4 text-center border border-green-100">
                        <div className="w-10 h-10 bg-green-600 rounded-lg mx-auto mb-2 flex items-center justify-center">
                          <span className="text-white font-bold text-sm">In</span>
                        </div>
                        <p className="text-xs font-medium text-slate-700">Indeed</p>
                      </div>
                      <div className="bg-emerald-50 rounded-xl p-4 text-center border border-emerald-100">
                        <div className="w-10 h-10 bg-emerald-600 rounded-lg mx-auto mb-2 flex items-center justify-center">
                          <span className="text-white font-bold text-sm">Gl</span>
                        </div>
                        <p className="text-xs font-medium text-slate-700">Glassdoor</p>
                      </div>
                      <div className="bg-purple-50 rounded-xl p-4 text-center border border-purple-100">
                        <div className="w-10 h-10 bg-purple-600 rounded-lg mx-auto mb-2 flex items-center justify-center">
                          <span className="text-white font-bold text-sm">Zi</span>
                        </div>
                        <p className="text-xs font-medium text-slate-700">ZipRecruiter</p>
                      </div>
                      <div className="bg-orange-50 rounded-xl p-4 text-center border border-orange-100">
                        <div className="w-10 h-10 bg-orange-600 rounded-lg mx-auto mb-2 flex items-center justify-center">
                          <span className="text-white font-bold text-sm">Co</span>
                        </div>
                        <p className="text-xs font-medium text-slate-700">Companies</p>
                      </div>
                      <div className="bg-indigo-50 rounded-xl p-4 text-center border border-indigo-100">
                        <div className="w-10 h-10 bg-indigo-600 rounded-lg mx-auto mb-2 flex items-center justify-center">
                          <span className="text-white font-bold text-sm">+</span>
                        </div>
                        <p className="text-xs font-medium text-slate-700">More</p>
                      </div>
                    </div>

                    <div className="flex items-center justify-center mb-4">
                      <svg className="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                      </svg>
                    </div>

                    <div className="bg-gradient-to-br from-slate-800 to-blue-900 rounded-xl p-6 text-white text-center">
                      <div className="flex items-center justify-center gap-2 mb-2">
                        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                          <Star className="text-white" size={20} />
                        </div>
                        <p className="font-bold text-lg">Career Attendant</p>
                      </div>
                      <p className="text-sm text-blue-200">Single Pane of Glass</p>
                    </div>
                  </div>
                  
                  <div className="absolute -top-4 -right-4 w-24 h-24 bg-blue-200 rounded-full blur-2xl opacity-50"></div>
                  <div className="absolute -bottom-4 -left-4 w-32 h-32 bg-purple-200 rounded-full blur-2xl opacity-50"></div>
                </div>
              </div>

              <div className="bg-white rounded-2xl p-10 shadow-sm border border-slate-200">
                <div className="grid grid-cols-3 gap-8 text-center">
                  <div>
                    <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                    </div>
                    <h4 className="text-xl font-bold text-slate-900 mb-2">Automatic Deduplication</h4>
                    <p className="text-slate-600">AI identifies and merges duplicate listings across platforms</p>
                  </div>
                  <div>
                    <div className="w-16 h-16 bg-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                      </svg>
                    </div>
                    <h4 className="text-xl font-bold text-slate-900 mb-2">Unified Application Tracking</h4>
                    <p className="text-slate-600">Track all applications regardless of original source</p>
                  </div>
                  <div>
                    <div className="w-16 h-16 bg-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
                      </svg>
                    </div>
                    <h4 className="text-xl font-bold text-slate-900 mb-2">Smart Recommendations</h4>
                    <p className="text-slate-600">Get notified of new relevant positions as they're posted</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Features Grid */}
          <div className="max-w-7xl mx-auto px-8 py-20">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-slate-900 mb-4">Everything You Need to Land Your Next Role</h2>
              <p className="text-xl text-slate-600">Powerful features designed to streamline your job search</p>
            </div>

            <div className="grid grid-cols-3 gap-8">
              <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 hover:shadow-lg transition">
                <div className="w-14 h-14 bg-blue-100 rounded-xl flex items-center justify-center mb-6">
                  <Star className="text-blue-600" size={28} />
                </div>
                <h3 className="text-2xl font-bold text-slate-900 mb-4">AI Job Fit Analysis</h3>
                <p className="text-slate-600 leading-relaxed">
                  Our AI evaluates how well each position matches your skills, experience, and career goals, helping you focus on the best opportunities.
                </p>
              </div>

              <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 hover:shadow-lg transition">
                <div className="w-14 h-14 bg-purple-100 rounded-xl flex items-center justify-center mb-6">
                  <Edit3 className="text-purple-600" size={28} />
                </div>
                <h3 className="text-2xl font-bold text-slate-900 mb-4">Targeted Resume Generator</h3>
                <p className="text-slate-600 leading-relaxed">
                  Automatically create customized resumes and cover letters tailored to each job posting, highlighting your most relevant qualifications.
                </p>
              </div>

              <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 hover:shadow-lg transition">
                <div className="w-14 h-14 bg-emerald-100 rounded-xl flex items-center justify-center mb-6">
                  <Calendar className="text-emerald-600" size={28} />
                </div>
                <h3 className="text-2xl font-bold text-slate-900 mb-4">Application Tracking</h3>
                <p className="text-slate-600 leading-relaxed">
                  Keep all your applications organized in one place. Track status, set reminders, and never miss an important follow-up or deadline.
                </p>
              </div>

              <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 hover:shadow-lg transition">
                <div className="w-14 h-14 bg-blue-100 rounded-xl flex items-center justify-center mb-6">
                  <TrendingUp className="text-blue-600" size={28} />
                </div>
                <h3 className="text-2xl font-bold text-slate-900 mb-4">Progress Dashboard</h3>
                <p className="text-slate-600 leading-relaxed">
                  Visualize your job search journey with comprehensive analytics. Track application stages, success rates, and identify patterns.
                </p>
              </div>

              <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 hover:shadow-lg transition">
                <div className="w-14 h-14 bg-indigo-100 rounded-xl flex items-center justify-center mb-6">
                  <Bookmark className="text-indigo-600" size={28} />
                </div>
                <h3 className="text-2xl font-bold text-slate-900 mb-4">Smart Organization</h3>
                <p className="text-slate-600 leading-relaxed">
                  Sort, filter, and prioritize jobs based on fit score, interest level, status, and more. Find what matters most, instantly.
                </p>
              </div>

              <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 hover:shadow-lg transition">
                <div className="w-14 h-14 bg-amber-100 rounded-xl flex items-center justify-center mb-6">
                  <MapPin className="text-amber-600" size={28} />
                </div>
                <h3 className="text-2xl font-bold text-slate-900 mb-4">Location & Remote Filtering</h3>
                <p className="text-slate-600 leading-relaxed">
                  Filter opportunities by location preferences and work arrangements. Focus on remote, hybrid, or onsite positions that fit your lifestyle.
                </p>
              </div>
            </div>
          </div>

          {/* CTA Section */}
          <div className="bg-gradient-to-br from-blue-600 to-blue-800 text-white">
            <div className="max-w-7xl mx-auto px-8 py-20 text-center">
              <h2 className="text-5xl font-bold mb-6">Ready to Accelerate Your Job Search?</h2>
              <p className="text-xl text-blue-100 mb-10 max-w-3xl mx-auto">
                Join thousands of job seekers who are landing their dream roles faster with Career Attendant's AI-powered tools.
              </p>
              <button 
                onClick={() => setCurrentPage('saved-jobs')}
                className="px-10 py-5 bg-white text-blue-600 rounded-xl hover:bg-blue-50 transition font-bold text-lg shadow-xl hover:shadow-2xl"
              >
                Get Started Now
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Detail View - Dashboard Style
  if (selectedJob) {
    return (
      <div className="min-h-screen bg-slate-50">
        {/* Top Bar */}
        <div className="bg-slate-900 text-slate-100 px-8 py-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <button 
              onClick={() => {
                setSelectedJob(null);
                setIsDescriptionExpanded(false);
                setIsEditingNotes(false);
              }}
              className="flex items-center gap-2 text-slate-300 hover:text-white transition"
            >
              <ArrowLeft size={20} />
              <span className="font-medium">Back to Jobs</span>
            </button>
            {isLoggedIn ? (
              <div className="relative">
                <button 
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="p-2 bg-slate-800 rounded-lg hover:bg-slate-700 transition"
                >
                  <User size={20} />
                </button>
                {showUserMenu && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-slate-200 py-2 z-10">
                    <button className="w-full text-left px-4 py-2 hover:bg-slate-50 text-slate-700">Profile</button>
                    <button className="w-full text-left px-4 py-2 hover:bg-slate-50 text-slate-700">Account</button>
                    <button className="w-full text-left px-4 py-2 hover:bg-slate-50 text-slate-700">Settings</button>
                    <div className="border-t border-slate-200 my-1"></div>
                    <button 
                      onClick={() => setIsLoggedIn(false)}
                      className="w-full text-left px-4 py-2 hover:bg-slate-50 text-red-600"
                    >
                      Logout
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button 
                onClick={() => setIsLoggedIn(true)}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium text-sm"
              >
                Login / Sign Up
              </button>
            )}
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-8 py-8">
          {/* Hero Section */}
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl shadow-xl p-10 mb-8 text-white">
            <div className="flex items-start justify-between mb-6">
              <div className="flex-1">
                <h1 className="text-5xl font-bold mb-4">{selectedJob.job_title}</h1>
                <div className="flex items-center gap-6 text-lg text-slate-300 mb-6">
                  <span className="font-semibold text-white">{selectedJob.company_name}</span>
                  <span className="flex items-center gap-2">
                    <MapPin size={20} />
                    {selectedJob.location}
                  </span>
                  <span className="flex items-center gap-2">
                    <Briefcase size={20} />
                    {formatLabel(selectedJob.remote_type)}
                  </span>
                </div>
                <div className="flex gap-3">
                  <span className={`px-4 py-2 rounded-lg text-sm font-semibold border-2 ${getStatusColorDetailed(selectedJob.application_status)}`}>
                    {formatLabel(selectedJob.application_status)}
                  </span>
                  <span className={`px-4 py-2 rounded-lg text-sm font-semibold border-2 ${
                    selectedJob.interest_level === 'high' ? 'bg-blue-300 text-blue-900 border-blue-500' :
                    selectedJob.interest_level === 'medium' ? 'bg-blue-200 text-blue-800 border-blue-400' :
                    'bg-blue-100 text-blue-700 border-blue-300'
                  }`}>
                    {formatLabel(selectedJob.interest_level)} Interest
                  </span>
                  <span className={`px-4 py-2 rounded-lg text-sm font-semibold border-2 whitespace-nowrap ${
                    selectedJob.job_fit_score === 'very_strong' ? 'bg-blue-400 text-blue-950 border-blue-600' :
                    selectedJob.job_fit_score === 'strong' ? 'bg-blue-300 text-blue-900 border-blue-500' :
                    selectedJob.job_fit_score === 'good' ? 'bg-blue-200 text-blue-800 border-blue-400' :
                    selectedJob.job_fit_score === 'fair' ? 'bg-blue-100 text-blue-700 border-blue-300' :
                    'bg-blue-50 text-blue-600 border-blue-200'
                  }`}>
                    {formatLabel(selectedJob.job_fit_score)} Fit
                  </span>
                </div>
              </div>
              <div className="text-right flex flex-col gap-3">
                <div>
                  <p className="text-sm text-slate-400 mb-1">APPLIED</p>
                  <p className="text-3xl font-bold">{selectedJob.application_date}</p>
                </div>
                <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium text-sm flex items-center gap-2 justify-center border-2 border-blue-600">
                  <ExternalLink size={16} />
                  View Original Posting
                </button>
              </div>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition">
              <div className="flex items-center justify-between mb-3">
                <DollarSign className="text-blue-600" size={32} />
              </div>
              <p className="text-sm text-slate-500 font-semibold uppercase mb-1">Salary Range</p>
              <p className="text-2xl font-bold text-slate-800">{selectedJob.salary_range}</p>
            </div>
            
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition">
              <div className="flex items-center justify-between mb-3">
                <Briefcase className="text-blue-600" size={32} />
              </div>
              <p className="text-sm text-slate-500 font-semibold uppercase mb-1">Work Type</p>
              <p className="text-2xl font-bold text-slate-800">{formatLabel(selectedJob.remote_type)}</p>
            </div>
            
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition">
              <div className="flex items-center justify-between mb-3">
                <TrendingUp className="text-blue-600" size={32} />
              </div>
              <p className="text-sm text-slate-500 font-semibold uppercase mb-1">Experience</p>
              <p className="text-2xl font-bold text-slate-800">{formatLabel(selectedJob.experience_level)}</p>
            </div>
            
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition">
              <div className="flex items-center justify-between mb-3">
                <Clock className="text-blue-600" size={32} />
              </div>
              <p className="text-sm text-slate-500 font-semibold uppercase mb-1">Employment</p>
              <p className="text-2xl font-bold text-slate-800">{formatLabel(selectedJob.role_type)}</p>
            </div>
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-3 gap-8">
            {/* Left Column */}
            <div className="col-span-2 space-y-8">
              {/* Job Description */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
                <h2 className="text-2xl font-bold text-slate-800 mb-6 flex items-center gap-3">
                  <div className="w-1 h-8 bg-blue-600 rounded"></div>
                  Position Overview
                </h2>
                <div className="prose max-w-none">
                  <p className={`text-slate-700 leading-relaxed text-lg whitespace-pre-line ${!isDescriptionExpanded ? 'line-clamp-6' : ''}`}>
                    {selectedJob.job_description}
                  </p>
                </div>
                <button 
                  onClick={() => setIsDescriptionExpanded(!isDescriptionExpanded)}
                  className="mt-4 text-blue-600 hover:text-blue-800 font-medium flex items-center gap-2"
                >
                  {isDescriptionExpanded ? '↑ Show Less' : '↓ Read More'}
                </button>
              </div>

              {/* My Notes */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-3">
                    <div className="w-1 h-8 bg-blue-500 rounded"></div>
                    My Notes
                  </h2>
                  <button 
                    onClick={() => setIsEditingNotes(!isEditingNotes)}
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition"
                  >
                    {isEditingNotes ? <Save size={18} /> : <Edit3 size={18} />}
                  </button>
                </div>
                {isEditingNotes ? (
                  <textarea 
                    value={selectedJob.notes}
                    onChange={(e) => handleChange(selectedJob.id, 'notes', e.target.value)}
                    className="w-full p-4 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent min-h-32 text-slate-700"
                  />
                ) : (
                  <p className="text-slate-700 leading-relaxed text-lg">{selectedJob.notes}</p>
                )}
              </div>

              {/* Application Timeline */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
                <h2 className="text-2xl font-bold text-slate-800 mb-6 flex items-center gap-3">
                  <div className="w-1 h-8 bg-blue-400 rounded"></div>
                  Application Progress
                </h2>
                <div className="space-y-6">
                  <div className="flex gap-4 items-start">
                    <div className="flex flex-col items-center">
                      <div className="w-4 h-4 bg-blue-500 rounded-full ring-4 ring-blue-100"></div>
                      <div className="w-0.5 h-16 bg-slate-200 mt-2"></div>
                    </div>
                    <div className="flex-1 pt-0.5">
                      <div className="flex items-center justify-between mb-1">
                        <p className="font-bold text-slate-800 text-lg">Application Submitted</p>
                        <span className="text-sm text-slate-500 font-medium">{selectedJob.application_date}</span>
                      </div>
                      <p className="text-slate-600">Successfully submitted application through company portal</p>
                    </div>
                  </div>
                  
                  <div className="flex gap-4 items-start">
                    <div className="flex flex-col items-center">
                      <div className="w-4 h-4 bg-blue-600 rounded-full ring-4 ring-blue-100"></div>
                      <div className="w-0.5 h-16 bg-slate-200 mt-2"></div>
                    </div>
                    <div className="flex-1 pt-0.5">
                      <div className="flex items-center justify-between mb-1">
                        <p className="font-bold text-slate-800 text-lg">Recruiter Screening</p>
                        <span className="text-sm text-slate-500 font-medium">2024-11-14</span>
                      </div>
                      <p className="text-slate-600">Phone screening completed - positive feedback received</p>
                    </div>
                  </div>
                  
                  <div className="flex gap-4 items-start">
                    <div className="flex flex-col items-center">
                      <div className="w-4 h-4 bg-slate-300 rounded-full ring-4 ring-slate-100"></div>
                    </div>
                    <div className="flex-1 pt-0.5">
                      <div className="flex items-center justify-between mb-1">
                        <p className="font-bold text-slate-800 text-lg">Technical Interview</p>
                        <span className="text-sm text-slate-500 font-medium">Upcoming</span>
                      </div>
                      <p className="text-slate-600">Scheduled for next week - system design focus</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column */}
            <div className="space-y-6">
              {/* Assessment */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <h3 className="text-xl font-bold text-slate-800 mb-4">Assessment</h3>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-slate-500 font-semibold uppercase mb-2">Interest Level</p>
                    <div className="flex gap-1">
                      {[1, 2, 3, 4, 5].map(i => (
                        <Star key={i} size={24} className={i <= 4 ? "fill-blue-400 text-blue-400" : "text-slate-300"} />
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-slate-500 font-semibold uppercase mb-2">Job Fit Score</p>
                    <div className="flex items-center gap-3 mb-3">
                      <div className="flex-1 bg-slate-200 h-3 rounded-full overflow-hidden">
                        <div className="bg-blue-600 h-full rounded-full" style={{width: selectedJob.job_fit_score === 'very_strong' ? '95%' : selectedJob.job_fit_score === 'strong' ? '85%' : selectedJob.job_fit_score === 'good' ? '70%' : selectedJob.job_fit_score === 'fair' ? '50%' : '30%'}}></div>
                      </div>
                      <span className="text-sm font-bold text-slate-700">{formatLabel(selectedJob.job_fit_score)}</span>
                    </div>
                    <div className={`rounded-lg p-4 border ${
                      selectedJob.job_fit_score === 'very_strong' || selectedJob.job_fit_score === 'strong' ? 'bg-blue-50 border-blue-200' :
                      selectedJob.job_fit_score === 'good' ? 'bg-blue-50 border-blue-200' :
                      'bg-slate-50 border-slate-200'
                    }`}>
                      <p className="text-sm text-slate-700 leading-relaxed">{selectedJob.job_fit_reason}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* AI-Generated Documents */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <h3 className="text-xl font-bold text-slate-800 mb-4">AI Documents</h3>
                <div className="space-y-3">
                  <a 
                    href={selectedJob.targeted_resume_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full px-4 py-3 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition font-medium flex items-center justify-between border border-blue-200"
                  >
                    <span>📄 Targeted Resume</span>
                    <ExternalLink size={16} />
                  </a>
                  <a 
                    href={selectedJob.targeted_cover_letter_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full px-4 py-3 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition font-medium flex items-center justify-between border border-blue-200"
                  >
                    <span>✉️ Cover Letter</span>
                    <ExternalLink size={16} />
                  </a>
                  <button className="w-full px-4 py-3 bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 transition font-medium border border-purple-200">
                    ✨ Regenerate Documents
                  </button>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <h3 className="text-xl font-bold text-slate-800 mb-4">Actions</h3>
                <div className="space-y-3">
                  <button className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium text-left flex items-center justify-between">
                    <span>Update Status</span>
                    <span>→</span>
                  </button>
                  <button className="w-full px-4 py-3 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition font-medium text-left flex items-center justify-between">
                    <span>Set Reminder</span>
                    <Calendar size={18} />
                  </button>
                  <button 
                    onClick={() => handleDelete(selectedJob.id)}
                    className="w-full px-4 py-3 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition font-medium text-left"
                  >
                    Delete Job
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Table View
  return (
    <div className="flex h-screen bg-slate-50">
      {/* Sidebar */}
      <div className={`${isNavExpanded ? 'w-72' : 'w-20'} bg-slate-900 text-slate-100 transition-all duration-300 flex flex-col shadow-xl`}>
        <div className="p-6 border-b border-slate-700">
          {isNavExpanded && (
            <div>
              <h1 className="text-2xl font-bold text-blue-400">Career Hub</h1>
              <p className="text-sm text-slate-400 mt-1">Track your applications</p>
            </div>
          )}
        </div>
        
        <nav className="flex-1 p-4 space-y-2">
          <button onClick={() => setCurrentPage('home')} className={`w-full flex items-center gap-4 p-4 rounded-lg transition ${currentPage === 'home' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800'}`}>
            <Home size={22} />
            {isNavExpanded && <span className="font-medium">Home</span>}
          </button>
          <button onClick={() => setCurrentPage('dashboard')} className={`w-full flex items-center gap-4 p-4 rounded-lg transition ${currentPage === 'dashboard' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800'}`}>
            <LayoutDashboard size={22} />
            {isNavExpanded && <span className="font-medium">Dashboard</span>}
          </button>
          <button onClick={() => setCurrentPage('saved-jobs')} className={`w-full flex items-center gap-4 p-4 rounded-lg transition ${currentPage === 'saved-jobs' ? 'bg-blue-600 text-white' : 'hover:bg-slate-800'}`}>
            <Bookmark size={22} />
            {isNavExpanded && <span className="font-medium">Saved Jobs</span>}
          </button>
        </nav>

        <button onClick={() => setIsNavExpanded(!isNavExpanded)} className="p-4 border-t border-slate-700 hover:bg-slate-800 flex items-center justify-center">
          {isNavExpanded ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
        </button>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <div className="p-10">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h2 className="text-4xl font-bold text-slate-800">Saved Jobs</h2>
              <p className="text-slate-500 mt-2">Manage and track your job applications</p>
            </div>
            <div className="flex flex-col items-end gap-3">
              {isLoggedIn ? (
                <div className="relative">
                  <button 
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="p-3 bg-slate-100 rounded-lg hover:bg-slate-200 transition"
                  >
                    <User size={20} className="text-slate-700" />
                  </button>
                  {showUserMenu && (
                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-slate-200 py-2 z-10">
                      <button className="w-full text-left px-4 py-2 hover:bg-slate-50 text-slate-700">Profile</button>
                      <button className="w-full text-left px-4 py-2 hover:bg-slate-50 text-slate-700">Account</button>
                      <button className="w-full text-left px-4 py-2 hover:bg-slate-50 text-slate-700">Settings</button>
                      <div className="border-t border-slate-200 my-1"></div>
                      <button 
                        onClick={() => setIsLoggedIn(false)}
                        className="w-full text-left px-4 py-2 hover:bg-slate-50 text-red-600"
                      >
                        Logout
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <button 
                  onClick={() => setIsLoggedIn(true)}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium text-sm"
                >
                  Login / Sign Up
                </button>
              )}
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium text-sm shadow-sm">
                + Add Job
              </button>
            </div>
          </div>
          
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-slate-100 border-b border-slate-200">
                    <th className="text-left p-5">
                      <button onClick={() => handleSort('job_title')} className="flex items-center gap-2 text-sm font-semibold text-slate-700 uppercase tracking-wider hover:text-slate-900">
                        Position
                        <SortIcon field="job_title" />
                      </button>
                    </th>
                    <th className="text-left p-5">
                      <button onClick={() => handleSort('company_name')} className="flex items-center gap-2 text-sm font-semibold text-slate-700 uppercase tracking-wider hover:text-slate-900">
                        Company
                        <SortIcon field="company_name" />
                      </button>
                    </th>
                    <th className="text-left p-5">
                      <button onClick={() => handleSort('application_status')} className="flex items-center gap-2 text-sm font-semibold text-slate-700 uppercase tracking-wider hover:text-slate-900">
                        Status
                        <SortIcon field="application_status" />
                      </button>
                    </th>
                    <th className="text-left p-5">
                      <button onClick={() => handleSort('interest_level')} className="flex items-center gap-2 text-sm font-semibold text-slate-700 uppercase tracking-wider hover:text-slate-900">
                        Interest
                        <SortIcon field="interest_level" />
                      </button>
                    </th>
                    <th className="text-left p-5">
                      <button onClick={() => handleSort('job_fit_score')} className="flex items-center gap-2 text-sm font-semibold text-slate-700 uppercase tracking-wider hover:text-slate-900">
                        Fit Score
                        <SortIcon field="job_fit_score" />
                      </button>
                    </th>
                    <th className="text-left p-5">
                      <button onClick={() => handleSort('application_date')} className="flex items-center gap-2 text-sm font-semibold text-slate-700 uppercase tracking-wider hover:text-slate-900">
                        Applied
                        <SortIcon field="application_date" />
                      </button>
                    </th>
                    <th className="text-left p-5">
                      <button onClick={() => handleSort('salary_range')} className="flex items-center gap-2 text-sm font-semibold text-slate-700 uppercase tracking-wider hover:text-slate-900">
                        Salary
                        <SortIcon field="salary_range" />
                      </button>
                    </th>
                    <th className="text-right p-5 text-sm font-semibold text-slate-700 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {sortedJobs.map(job => (
                    <tr key={job.id} className="hover:bg-slate-50 transition">
                      <td className="p-5">
                        <button 
                          onClick={() => setSelectedJob(job)}
                          className="font-medium text-blue-600 hover:text-blue-800 hover:underline text-left"
                        >
                          {job.job_title}
                        </button>
                      </td>
                      <td className="p-5">
                        <span className="text-slate-700">{job.company_name}</span>
                      </td>
                      <td className="p-5">
                        <span className={`inline-flex px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(job.application_status)}`}>
                          {formatLabel(job.application_status)}
                        </span>
                      </td>
                      <td className="p-5">
                        <span className={`inline-flex px-3 py-1 rounded-full text-xs font-semibold ${getInterestColor(job.interest_level)}`}>
                          {formatLabel(job.interest_level)}
                        </span>
                      </td>
                      <td className="p-5">
                        <span className={`inline-flex px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap ${getFitColor(job.job_fit_score)}`}>
                          {formatLabel(job.job_fit_score)}
                        </span>
                      </td>
                      <td className="p-5">
                        <span className="text-slate-600 text-sm">{job.application_date}</span>
                      </td>
                      <td className="p-5">
                        <span className="font-medium text-slate-800">{job.salary_range}</span>
                      </td>
                      <td className="p-5 text-right">
                        <div className="flex gap-2 justify-end">
                          <button className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition">
                            <Edit2 size={18} />
                          </button>
                          <button onClick={() => handleDelete(job.id)} className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition">
                            <Trash2 size={18} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}