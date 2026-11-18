const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🌸 [FLOWER HAPPY] Starting Setup...');

// 1. Copy .env.example to .env if not exists
if (!fs.existsSync('.env')) {
  if (fs.existsSync('.env.example')) {
    fs.copyFileSync('.env.example', '.env');
    console.log('✅ Created .env from .env.example');
  }
} else {
  console.log('ℹ️  .env already exists');
}

// 2. Python Virtual Environment Check & Setup
const isWindows = process.platform === 'win32';
const venvPath = path.join(__dirname, '..', 'venv');
const pythonCmd = isWindows ? path.join(venvPath, 'Scripts', 'python.exe') : path.join(venvPath, 'bin', 'python');

if (!fs.existsSync(venvPath)) {
  console.log('📦 Creating Python virtual environment...');
  execSync('python -m venv venv', { stdio: 'inherit' });
} else {
  console.log('ℹ️  Python virtual environment exists at ./venv');
}

// 3. Install backend requirements
console.log('📦 Installing backend dependencies...');
execSync(`"${pythonCmd}" -m pip install -r backend/requirements.txt`, { stdio: 'inherit' });

// 4. Install frontend dependencies
console.log('📦 Installing frontend dependencies...');
execSync('cd frontend && npm install', { stdio: 'inherit' });

console.log('🎉 [FLOWER HAPPY] Setup completed successfully! Run "npm run dev" to start.');
