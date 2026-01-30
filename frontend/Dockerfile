FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install ALL dependencies (need devDeps for build)
RUN npm ci

# Copy application code
COPY . .

# Build argument for API URL (Railway will inject this)
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build the application
RUN npm run build

# Expose port
EXPOSE 3000

# Start production server
CMD ["npm", "start"]
