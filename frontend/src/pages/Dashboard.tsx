import { useState, useRef } from 'react'
import { useFHIRExtraction } from '../hooks/useFHIR'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { Upload, FileText, Download, Copy, CheckCircle, AlertCircle } from 'lucide-react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism'
import toast from 'react-hot-toast'

export default function Dashboard() {
  const [dragActive, setDragActive] = useState(false)
  const [copied, setCopied] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { extractFHIR, isLoading, data: fhirData } = useFHIRExtraction()

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleFile = (file: File) => {
    if (!file.type.includes('pdf') && !file.type.includes('text')) {
      toast.error('Please upload a PDF or text file')
      return
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB limit
      toast.error('File size must be less than 10MB')
      return
    }

    extractFHIR(file)
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const copyToClipboard = async () => {
    if (fhirData) {
      try {
        await navigator.clipboard.writeText(JSON.stringify(fhirData, null, 2))
        setCopied(true)
        toast.success('Copied to clipboard!')
        setTimeout(() => setCopied(false), 2000)
      } catch (err) {
        toast.error('Failed to copy to clipboard')
      }
    }
  }

  const downloadJSON = () => {
    if (fhirData) {
      const blob = new Blob([JSON.stringify(fhirData, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'fhir-extraction.json'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      toast.success('Download started!')
    }
  }

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">FHIR Data Extraction</h1>
          <p className="mt-2 text-gray-600">
            Upload a clinical document to extract structured FHIR data
          </p>
        </div>

        <div className="grid gap-6">
          {/* Upload Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Upload className="mr-2 h-5 w-5" />
                Upload Clinical Document
              </CardTitle>
              <CardDescription>
                Drag and drop a PDF or text file, or click to browse
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  dragActive
                    ? 'border-blue-400 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <FileText className="mx-auto h-12 w-12 text-gray-400" />
                <div className="mt-4">
                  <p className="text-lg font-medium text-gray-900">
                    {dragActive ? 'Drop your file here' : 'Upload a clinical document'}
                  </p>
                  <p className="text-sm text-gray-500">
                    PDF or text files up to 10MB
                  </p>
                </div>
                <div className="mt-6">
                  <Button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isLoading}
                    className="mr-3"
                  >
                    {isLoading ? 'Processing...' : 'Choose File'}
                  </Button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.txt"
                    onChange={handleFileInput}
                    className="hidden"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Results Section */}
          {fhirData && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <CheckCircle className="mr-2 h-5 w-5 text-green-500" />
                  Extraction Results
                </CardTitle>
                <CardDescription>
                  FHIR Bundle with {fhirData.entry?.length || 0} resources extracted
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="mb-4 flex space-x-2">
                  <Button onClick={copyToClipboard} variant="outline" size="sm">
                    {copied ? (
                      <>
                        <CheckCircle className="mr-2 h-4 w-4" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="mr-2 h-4 w-4" />
                        Copy JSON
                      </>
                    )}
                  </Button>
                  <Button onClick={downloadJSON} variant="outline" size="sm">
                    <Download className="mr-2 h-4 w-4" />
                    Download
                  </Button>
                </div>

                <div className="border rounded-lg overflow-hidden">
                  <SyntaxHighlighter
                    language="json"
                    style={tomorrow}
                    customStyle={{
                      margin: 0,
                      fontSize: '14px',
                      maxHeight: '500px',
                    }}
                    showLineNumbers
                    wrapLines
                  >
                    {JSON.stringify(fhirData, null, 2)}
                  </SyntaxHighlighter>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Instructions */}
          <Card>
            <CardHeader>
              <CardTitle>How it works</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-blue-600">1</span>
                  </div>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">Upload Document</h3>
                  <p className="text-sm text-gray-600">
                    Upload a PDF or text file containing clinical information
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-blue-600">2</span>
                  </div>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">AI Processing</h3>
                  <p className="text-sm text-gray-600">
                    Our AI analyzes the document and extracts structured medical data
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-blue-600">3</span>
                  </div>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">FHIR Output</h3>
                  <p className="text-sm text-gray-600">
                    Receive standardized FHIR R4 JSON with Patient, Observation, Condition, and Medication resources
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
