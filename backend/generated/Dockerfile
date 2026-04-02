
# Use an official Node.js runtime as a parent image.
# We choose `lts-alpine` for long-term support and a smaller image size.
FROM node:lts-alpine

# Set the working directory inside the container.
# All subsequent commands will run from this directory.
WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock) into the working directory.
# This step is done separately to leverage Docker's build cache.
# If only application code changes, but dependencies remain the same,
# Docker will use the cached layer for dependency installation, speeding up builds.
COPY package*.json ./

# Install application dependencies.
# `npm ci` is preferred in CI/CD environments and Dockerfiles because it
# installs dependencies strictly based on `package-lock.json`, ensuring consistent builds.
# `--only=production` ensures only production dependencies are installed, keeping the image smaller.
RUN npm ci --only=production

# Copy the rest of the application source code into the working directory.
COPY . .

# Expose the port that your Node.js application listens on.
# Common ports are 3000, 8080. Adjust this value if your application uses a different port.
EXPOSE 3000

# Define the command to run your application when the container starts.
# This assumes you have a "start" script defined in your package.json (e.g., "start": "node index.js").
CMD ["npm", "run", "dev"]
