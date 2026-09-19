# ==============================================================================
# RoleFlow — Frontend Container Scaffolding (Template Only)
# ==============================================================================
# NOTE: This Dockerfile is provided as unconfigured architectural scaffolding.
# It is NOT integrated into the active runtime environment.
#
# Primary runtime execution:
#   cd frontend && npm run dev
# ==============================================================================

FROM node:20-alpine AS build

WORKDIR /app

# Copy dependency specifications
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source code
COPY . .

# Build production assets
RUN npm run build

# Production static serving stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
