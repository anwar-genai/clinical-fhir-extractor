import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useApiKeys } from '../hooks/useApiKeys'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { Key, Plus, Trash2, Copy, Eye, EyeOff, Calendar, Clock } from 'lucide-react'
import toast from 'react-hot-toast'

const apiKeySchema = z.object({
  name: z.string().min(3, 'Name must be at least 3 characters'),
  expires_in_days: z.number().min(1).max(365).optional(),
})

type ApiKeyForm = z.infer<typeof apiKeySchema>

export default function ApiKeys() {
  const [showKey, setShowKey] = useState<number | null>(null)
  const [newKey, setNewKey] = useState<string | null>(null)
  const { apiKeys, isLoading, createApiKey, deleteApiKey, isCreating, isDeleting } = useApiKeys()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ApiKeyForm>({
    resolver: zodResolver(apiKeySchema),
  })

  const onSubmit = (data: ApiKeyForm) => {
    createApiKey(data, {
      onSuccess: (response) => {
        setNewKey(response.key)
        reset()
        toast.success('API key created successfully!')
      },
    })
  }

  const handleDelete = (keyId: number) => {
    if (window.confirm('Are you sure you want to delete this API key?')) {
      deleteApiKey(keyId)
    }
  }

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      toast.success('Copied to clipboard!')
    } catch (err) {
      toast.error('Failed to copy to clipboard')
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  const isExpired = (expiresAt?: string) => {
    if (!expiresAt) return false
    return new Date(expiresAt) < new Date()
  }

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">API Keys</h1>
          <p className="mt-2 text-gray-600">
            Manage your API keys for programmatic access to the FHIR extractor
          </p>
        </div>

        <div className="grid gap-6">
          {/* Create New API Key */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Plus className="mr-2 h-5 w-5" />
                Create New API Key
              </CardTitle>
              <CardDescription>
                Generate a new API key for programmatic access
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                    Key Name
                  </label>
                  <Input
                    id="name"
                    {...register('name')}
                    placeholder="e.g., My Automation Script"
                    className="mt-1"
                  />
                  {errors.name && (
                    <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="expires_in_days" className="block text-sm font-medium text-gray-700">
                    Expires In (Days) - Optional
                  </label>
                  <Input
                    id="expires_in_days"
                    type="number"
                    min="1"
                    max="365"
                    {...register('expires_in_days', { valueAsNumber: true })}
                    placeholder="Leave empty for no expiration"
                    className="mt-1"
                  />
                  {errors.expires_in_days && (
                    <p className="mt-1 text-sm text-red-600">{errors.expires_in_days.message}</p>
                  )}
                </div>

                <Button type="submit" disabled={isCreating}>
                  {isCreating ? 'Creating...' : 'Create API Key'}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* New Key Display */}
          {newKey && (
            <Card className="border-green-200 bg-green-50">
              <CardHeader>
                <CardTitle className="text-green-800">API Key Created!</CardTitle>
                <CardDescription className="text-green-600">
                  Save this key securely - it won't be shown again
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center space-x-2">
                  <Input
                    value={newKey}
                    readOnly
                    className="font-mono text-sm"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyToClipboard(newKey)}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
                <p className="mt-2 text-sm text-green-600">
                  ⚠️ This is the only time you'll see this key. Copy it now!
                </p>
              </CardContent>
            </Card>
          )}

          {/* API Keys List */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Key className="mr-2 h-5 w-5" />
                Your API Keys
              </CardTitle>
              <CardDescription>
                Manage your existing API keys
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-600">Loading API keys...</p>
                </div>
              ) : apiKeys && apiKeys.length > 0 ? (
                <div className="space-y-4">
                  {apiKeys.map((key) => (
                    <div
                      key={key.id}
                      className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <h3 className="font-medium text-gray-900">{key.name}</h3>
                            {!key.is_active && (
                              <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded">
                                Inactive
                              </span>
                            )}
                            {key.expires_at && isExpired(key.expires_at) && (
                              <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded">
                                Expired
                              </span>
                            )}
                          </div>
                          <div className="mt-2 flex items-center space-x-4 text-sm text-gray-600">
                            <div className="flex items-center space-x-1">
                              <Calendar className="h-4 w-4" />
                              <span>Created: {formatDate(key.created_at)}</span>
                            </div>
                            {key.expires_at && (
                              <div className="flex items-center space-x-1">
                                <Clock className="h-4 w-4" />
                                <span>Expires: {formatDate(key.expires_at)}</span>
                              </div>
                            )}
                            {key.last_used_at && (
                              <div className="flex items-center space-x-1">
                                <span>Last used: {formatDate(key.last_used_at)}</span>
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setShowKey(showKey === key.id ? null : key.id)}
                          >
                            {showKey === key.id ? (
                              <EyeOff className="h-4 w-4" />
                            ) : (
                              <Eye className="h-4 w-4" />
                            )}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDelete(key.id)}
                            disabled={isDeleting}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                      {showKey === key.id && (
                        <div className="mt-3 p-3 bg-gray-100 rounded">
                          <p className="text-sm text-gray-600 mb-2">API Key:</p>
                          <div className="flex items-center space-x-2">
                            <code className="flex-1 text-sm font-mono bg-white p-2 rounded border">
                              {key.key || '••••••••••••••••••••••••••••••••'}
                            </code>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => copyToClipboard(key.key || '')}
                            >
                              <Copy className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Key className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No API keys</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Create your first API key to get started with programmatic access.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Usage Instructions */}
          <Card>
            <CardHeader>
              <CardTitle>How to Use API Keys</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-medium text-gray-900">Authentication</h3>
                <p className="text-sm text-gray-600">
                  Include your API key in the Authorization header:
                </p>
                <code className="block mt-2 p-2 bg-gray-100 rounded text-sm font-mono">
                  Authorization: Bearer YOUR_API_KEY
                </code>
              </div>

              <div>
                <h3 className="font-medium text-gray-900">Example Usage</h3>
                <pre className="mt-2 p-3 bg-gray-100 rounded text-sm overflow-x-auto">
{`curl -X POST "http://localhost:8000/extract-fhir" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -F "file=@clinical_note.pdf"`}
                </pre>
              </div>

              <div>
                <h3 className="font-medium text-gray-900">Security Best Practices</h3>
                <ul className="mt-2 text-sm text-gray-600 space-y-1">
                  <li>• Store API keys securely and never commit them to version control</li>
                  <li>• Use environment variables to store keys in production</li>
                  <li>• Set expiration dates for keys that don't need permanent access</li>
                  <li>• Delete unused keys to minimize security risks</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
