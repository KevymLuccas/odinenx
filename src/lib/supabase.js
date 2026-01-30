import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://mzamszcpbverpadjelck.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im16YW1zemNwYnZlcnBhZGplbGNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk3OTA5NjIsImV4cCI6MjA4NTM2Njk2Mn0.I8uUlJxgm2UgyavzRA6ATcaoV3SRVd9Z-NgeENzzUN4'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
