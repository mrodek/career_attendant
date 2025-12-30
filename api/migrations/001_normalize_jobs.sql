-- Migration: Normalize SavedJob table - Add Job table
-- Run this in DBCode notebook

-- 1. Create the jobs table
CREATE TABLE jobs (
    id VARCHAR(36) PRIMARY KEY,
    job_title VARCHAR(255),
    company_name VARCHAR(255),
    job_url VARCHAR(2048) NOT NULL UNIQUE,
    job_description TEXT,
    salary_range VARCHAR(100),
    location VARCHAR(255),
    remote_type VARCHAR(50),
    role_type VARCHAR(50),
    experience_level VARCHAR(50),
    company_logo_url VARCHAR(2048),
    industry VARCHAR(100),
    required_skills JSONB,
    posting_date TIMESTAMPTZ,
    expiration_date TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    source VARCHAR(100),
    scraped_data JSONB,
    saved_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ
);

CREATE INDEX ix_jobs_job_url ON jobs(job_url);
CREATE INDEX ix_jobs_company_name ON jobs(company_name);

-- 2. Add new columns to saved_jobs
ALTER TABLE saved_jobs ADD COLUMN job_id VARCHAR(36);

-- AI job fit assessment
ALTER TABLE saved_jobs ADD COLUMN job_fit_score INTEGER;
ALTER TABLE saved_jobs ADD COLUMN job_fit_reason TEXT;
ALTER TABLE saved_jobs ADD COLUMN job_fit_assessed_at TIMESTAMPTZ;

-- AI-generated documents
ALTER TABLE saved_jobs ADD COLUMN targeted_resume_url VARCHAR(2048);
ALTER TABLE saved_jobs ADD COLUMN targeted_resume_drive_id VARCHAR(255);
ALTER TABLE saved_jobs ADD COLUMN targeted_cover_letter_url VARCHAR(2048);
ALTER TABLE saved_jobs ADD COLUMN targeted_cover_letter_drive_id VARCHAR(255);
ALTER TABLE saved_jobs ADD COLUMN documents_generated_at TIMESTAMPTZ;

-- AI workflow status
ALTER TABLE saved_jobs ADD COLUMN ai_workflow_status VARCHAR(50);
ALTER TABLE saved_jobs ADD COLUMN ai_workflow_error TEXT;

-- Application outcome
ALTER TABLE saved_jobs ADD COLUMN rejection_reason TEXT;
ALTER TABLE saved_jobs ADD COLUMN interview_dates JSONB;
ALTER TABLE saved_jobs ADD COLUMN salary_offered VARCHAR(100);
ALTER TABLE saved_jobs ADD COLUMN referral_contact VARCHAR(255);

-- Additional tracking
ALTER TABLE saved_jobs ADD COLUMN application_date TIMESTAMPTZ;
ALTER TABLE saved_jobs ADD COLUMN reminder_date TIMESTAMPTZ;
ALTER TABLE saved_jobs ADD COLUMN priority_rank INTEGER;

-- 3. Migrate existing data: Create jobs from saved_jobs
INSERT INTO jobs (id, job_url, job_title, company_name, job_description, salary_range, location, remote_type, role_type, source, saved_count, is_active, created_at)
SELECT 
    gen_random_uuid()::text,
    job_url,
    job_title,
    company_name,
    job_description,
    salary_range,
    location,
    remote_type,
    role_type,
    source,
    1,
    TRUE,
    MIN(created_at)
FROM saved_jobs
WHERE job_url IS NOT NULL
GROUP BY job_url, job_title, company_name, job_description, salary_range, location, remote_type, role_type, source;

-- 4. Update saved_jobs with job_id references
UPDATE saved_jobs s
SET job_id = j.id
FROM jobs j
WHERE s.job_url = j.job_url;

-- 5. Add constraints
ALTER TABLE saved_jobs ADD CONSTRAINT fk_saved_jobs_job_id FOREIGN KEY (job_id) REFERENCES jobs(id);
ALTER TABLE saved_jobs ADD CONSTRAINT uq_user_job UNIQUE (user_id, job_id);

-- 6. Drop old columns from saved_jobs (optional - can do later)
-- ALTER TABLE saved_jobs DROP COLUMN job_title;
-- ALTER TABLE saved_jobs DROP COLUMN company_name;
-- ALTER TABLE saved_jobs DROP COLUMN job_description;
-- ALTER TABLE saved_jobs DROP COLUMN salary_range;
-- ALTER TABLE saved_jobs DROP COLUMN location;
-- ALTER TABLE saved_jobs DROP COLUMN remote_type;
-- ALTER TABLE saved_jobs DROP COLUMN role_type;
-- ALTER TABLE saved_jobs DROP COLUMN source;
