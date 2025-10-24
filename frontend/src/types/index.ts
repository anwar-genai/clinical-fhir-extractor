export interface User {
  id: number
  email: string
  username: string
  full_name?: string
  role: 'user' | 'researcher' | 'clinician' | 'admin'
  is_active: boolean
  is_verified: boolean
  created_at: string
  last_login?: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  email: string
  username: string
  password: string
  full_name?: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface ApiKey {
  id: number
  key: string
  name: string
  created_at: string
  expires_at?: string
}

export interface ApiKeyCreate {
  name: string
  expires_in_days?: number
}

export interface ApiKeyListItem {
  id: number
  name: string
  is_active: boolean
  created_at: string
  expires_at?: string
  last_used_at?: string
}

export interface AuditLog {
  id: number
  user_id?: number
  action: string
  resource?: string
  status: string
  ip_address?: string
  created_at: string
}

export interface FHIRBundle {
  resourceType: string
  type: string
  entry: Array<{
    resource: {
      resourceType: string
      id: string
      [key: string]: any
    }
  }>
}

export interface ExtractionListItem {
  id: number
  filename: string
  created_at: string
}

export interface ExtractionResponse {
  id: number
  user_id: number
  filename: string
  content_type?: string
  file_size?: number
  result_json: string
  created_at: string
}

export interface FHIRExtractionResponse {
  extraction_id: number
  bundle: FHIRBundle
}
