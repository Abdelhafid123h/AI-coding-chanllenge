# RAG Q&A Chatbot

A Retrieval-Augmented Generation (RAG) application that answers questions based on provided documents using FastAPI, Next.js, and Docker.

## 🚀 Features

- **Document Ingestion**: Supports PDF, TXT, and Markdown files
- **RAG Pipeline**: Full implementation with embeddings, chunking, and vector store
- **FastAPI Backend**: RESTful API with POST /ask endpoint
- **Next.js Frontend**: Modern chat interface with TypeScript
- **Docker Ready**: Complete containerization with management scripts
- **Source Citations**: Displays source documents for answers

## 📋 Requirements

- Docker Desktop
- 4GB+ RAM
- Internet connection (for model downloads)

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Next.js   │─────▶│   FastAPI    │─────▶│   FAISS     │
│   Frontend  │      │   Backend    │      │ Vector Store│
│   (Port 3000)│      │  (Port 8000) │      │             │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  LangChain   │
                     │  RAG Pipeline│
                     └──────────────┘
```

### Components

**Backend:**
- FastAPI with automatic API documentation
- LangChain for RAG pipeline
- FAISS vector store
- HuggingFace embeddings (sentence-transformers)
- Support for PDF, TXT, and MD files

**Frontend:**
- Next.js 14 with TypeScript
- Real-time chat interface
- Source citation display
- Responsive design

**Infrastructure:**
- Docker Compose orchestration
- Persistent vector store
- Bash management script

## 📦 Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd AI\ Coding\ Challenge
```

### 2. Verify Documents

Ensure your documents are in the `provided document/` directory:

```bash
ls "provided document/"
```

### 3. Build Containers

```bash
chmod +x docker.sh
./docker.sh build
```

This will:
- Build backend Python container
- Build frontend Node.js container
- Download dependencies

**Time:** 3-5 minutes (first time)

### 4. Start Services

```bash
./docker.sh up
```

Services will be available at:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### 5. Ingest Documents

```bash
./docker.sh ingest
```

This process:
- Loads documents from `provided document/`
- Splits into chunks (1000 chars, 200 overlap)
- Generates embeddings
- Stores in FAISS vector database

**Time:** 30-90 seconds depending on document size

### 6. Start Asking Questions!

Open your browser: http://localhost:3000

Example questions:
- "What is this document about?"
- "Summarize the main points"
- "Tell me about [specific topic]"

## 🎮 Docker Commands

```bash
./docker.sh build      # Build containers
./docker.sh up         # Start services
./docker.sh down       # Stop services
./docker.sh ingest     # Run document ingestion
./docker.sh logs       # View all logs
./docker.sh logs backend   # View backend logs only
./docker.sh status     # Show service status
./docker.sh restart    # Restart all services
./docker.sh clean      # Remove all containers and volumes
./docker.sh help       # Show help
```

## 🔌 API Usage

### Ask a Question

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?"}'
```

**Response:**
```json
{
  "answer": "Based on the documents...",
  "sources": ["Schatzinsel_E.pdf"]
}
```

### Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "vector_store_initialized": true
}
```

## 📁 Project Structure

```
.
├── backend/
│   ├── main.py              # FastAPI application
│   ├── rag_pipeline.py      # RAG implementation
│   ├── ingest.py            # Document ingestion
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Backend container
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # Main chat UI
│   │   ├── layout.tsx       # App layout
│   │   ├── page.module.css  # Styles
│   │   └── globals.css      # Global styles
│   ├── package.json         # Node dependencies
│   ├── tsconfig.json        # TypeScript config
│   └── Dockerfile           # Frontend container
├── provided document/       # Your documents
├── docker-compose.yml       # Service orchestration
├── docker.sh                # Management script
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## 🔧 Configuration

### Environment Variables

Create `.env` file (optional):

```env
HUGGINGFACE_API_TOKEN=your_token_here  # Optional: for better LLM responses
```

### Chunking Parameters

Edit `backend/rag_pipeline.py`:

```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,      # Adjust chunk size
    chunk_overlap=200,    # Adjust overlap
    length_function=len,
)
```

### Embedding Model

Edit `backend/rag_pipeline.py`:

```python
self.embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"  # Change model
)
```

## 🐛 Troubleshooting

### Docker Issues

```bash
# Check Docker is running
docker info

# View logs
./docker.sh logs

# Clean and rebuild
./docker.sh clean
./docker.sh build
./docker.sh up
```

### "Vector store not initialized"

```bash
# Run ingestion
./docker.sh ingest

# Check backend logs
./docker.sh logs backend
```

### Port Already in Use

```bash
# Stop conflicting services
./docker.sh down

# Or change ports in docker-compose.yml
```

### Slow Responses

- First query loads the model (~90MB)
- Subsequent queries are faster
- Consider adding HuggingFace API token

## 📊 Performance

- **Ingestion:** ~30-60 seconds per 100 pages
- **Query Time:** 2-5 seconds (with HuggingFace Hub)
- **Memory:** ~2GB backend, ~500MB frontend
- **Storage:** ~10MB per 1000 chunks

## 🔒 Security Notes

- No authentication implemented (demo purposes)
- CORS enabled for all origins (development)
- For production, add authentication and restrict CORS

## 🚀 Future Improvements

- [ ] Add authentication
- [ ] Implement conversation history
- [ ] Support more document formats
- [ ] Add semantic caching
- [ ] Implement streaming responses
- [ ] Multi-language support

## 📝 Technical Decisions

### Why FAISS?
- Fast, local similarity search
- No external service required
- Persistent storage
- No API costs

### Why sentence-transformers?
- Good quality embeddings
- No API key required
- Fast inference
- Compact model size

### Why HuggingFace Hub?
- Free tier available
- Multiple model options
- Fallback to retrieval-only mode

## 👤 Author

**KBIRI ALAOUI Abdelhafid**
- Challenge: Quorium AI Engineer Trainee
- Branch: `challenge/kbiri-alaoui-abdelhafid`
- Date: December 2025

## 📄 License

This project is created for the Quorium AI Engineer Trainee coding challenge.

---

**Built for the Quorium AI Engineer Trainee Challenge** 🚀
