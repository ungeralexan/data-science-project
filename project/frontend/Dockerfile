# Use Node 22 as base
ARG NODE_VERSION=22
FROM node:${NODE_VERSION}

# Create app directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy all project files
COPY . .

# Start Vite dev server, listen on 0.0.0.0:5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
