FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install ALL dependencies (need devDeps for build)
RUN npm ci

# Copy application code
COPY . .

# Build argument with DEFAULT value pointing to Render backend
ARG NEXT_PUBLIC_API_URL=https://tavi-backend.onrender.com
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Debug: Print the API URL being used
RUN echo "🔍 Building with API URL: $NEXT_PUBLIC_API_URL"

# Build the application
RUN npm run build

# Expose port
EXPOSE 3000

# Start production server
CMD ["npm", "start"]
