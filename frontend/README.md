# Clinical FHIR Extractor - Frontend

Modern React frontend for the Clinical FHIR Extractor application with authentication, file upload, and admin dashboard.

## Features

- 🔐 **Authentication System**
  - User registration and login
  - JWT token management with automatic refresh
  - API key management for programmatic access
  - Role-based access control (USER, RESEARCHER, CLINICIAN, ADMIN)

- 📄 **FHIR Extraction Interface**
  - Drag & drop file upload
  - Real-time extraction progress
  - Syntax-highlighted JSON output
  - Copy to clipboard and download functionality

- 👑 **Admin Dashboard**
  - User management and statistics
  - Audit log viewer with filtering
  - System activity monitoring
  - CSV export functionality

- 🎨 **Modern UI/UX**
  - Responsive design with Tailwind CSS
  - Dark/light mode support
  - Loading states and error handling
  - Toast notifications

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **React Router** for navigation
- **TanStack Query** for server state management
- **React Hook Form** with Zod validation
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **React Syntax Highlighter** for code display

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm, yarn, or pnpm

### Installation

```bash
# Install dependencies
npm install

# Or with yarn
yarn install

# Or with pnpm
pnpm install
```

### Development

```bash
# Start development server
npm run dev

# Or with yarn
yarn dev

# Or with pnpm
pnpm dev
```

The app will be available at `http://localhost:3000`

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

```env
# API Configuration
VITE_API_URL=http://localhost:8000

# Optional: Enable debug mode
VITE_DEBUG=false
```

### Building for Production

```bash
# Build the app
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── ui/             # Base UI components (Button, Input, Card)
│   │   ├── Layout.tsx      # Main layout with sidebar
│   │   └── LoadingSpinner.tsx
│   ├── hooks/              # Custom React hooks
│   │   ├── useAuth.ts      # Authentication logic
│   │   ├── useFHIR.ts      # FHIR extraction
│   │   └── useApiKeys.ts   # API key management
│   ├── pages/              # Page components
│   │   ├── Login.tsx       # Login page
│   │   ├── Register.tsx   # Registration page
│   │   ├── Dashboard.tsx   # Main FHIR extraction interface
│   │   ├── Profile.tsx     # User profile management
│   │   ├── ApiKeys.tsx     # API key management
│   │   ├── AdminDashboard.tsx # Admin overview
│   │   └── AuditLogs.tsx   # Audit log viewer
│   ├── lib/                # Utilities and configurations
│   │   └── api.ts          # Axios configuration
│   ├── types/              # TypeScript type definitions
│   │   └── index.ts        # Shared types
│   ├── App.tsx             # Main app component
│   ├── main.tsx            # App entry point
│   └── index.css           # Global styles
├── public/                 # Static assets
├── package.json            # Dependencies and scripts
├── vite.config.ts          # Vite configuration
├── tailwind.config.js      # Tailwind CSS configuration
└── tsconfig.json           # TypeScript configuration
```

## API Integration

The frontend communicates with the backend API through:

- **Authentication**: JWT tokens with automatic refresh
- **File Upload**: Multipart form data for FHIR extraction
- **Real-time Updates**: React Query for caching and synchronization
- **Error Handling**: Comprehensive error boundaries and user feedback

## Deployment

### Build for Production

```bash
npm run build
```

This creates a `dist/` folder with optimized production assets.

### Deploy to Static Hosting

The built app can be deployed to any static hosting service:

- **Vercel**: `vercel --prod`
- **Netlify**: Drag and drop the `dist/` folder
- **AWS S3**: Upload `dist/` contents to S3 bucket
- **GitHub Pages**: Use GitHub Actions for automated deployment

### Environment Variables for Production

Set these environment variables in your hosting platform:

```env
VITE_API_URL=https://your-api-domain.com
VITE_DEBUG=false
```

## Development Scripts

```bash
# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type checking
npm run type-check

# Linting
npm run lint
```

## Contributing

1. Follow the existing code style
2. Use TypeScript for all new code
3. Add proper error handling
4. Write meaningful commit messages
5. Test your changes thoroughly

## License

MIT License - see LICENSE file for details
