// Public site configuration.
//
// The Supabase key below is the PUBLIC anon key. It is meant to be shipped in
// client code: it only identifies the project as the anonymous role. It is safe
// in the static bundle because the beta_signups table has insert-only RLS, so
// this key can add a signup but can never read, change or delete the list.
// NEVER put the service_role key here.

export const DOWNLOAD_URL = 'https://downloads.omnidj.com/Omni-DJ-1.0.0.dmg';

export const SUPABASE_URL = 'https://lbabsffxefkrxwzkbzar.supabase.co';

export const SUPABASE_ANON_KEY =
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxiYWJzZmZ4ZWZrcnh3emtiemFyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzgwODEyNDksImV4cCI6MjA5MzY1NzI0OX0.4_T3oIvMLdGRtpZXISNbEub1V0LVISNDwXe8DZHSaS0';
