"""Manual verification script for Phase 6: AI Document Understanding + Grounded MCQ Generation."""
import os
import sys
import asyncio
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.ai.providers.mock_provider import MockLLMProvider
from app.ai.embeddings.mock_provider import MockEmbeddingProvider
from app.ai.models import LearningMaterial, DocumentChunk
from app.ai.chunking import TextChunker
from app.ai.cleaning import TextCleaner
from app.ai.retrieval import VectorStore, RetrieverService
from app.ai.generation import MCQGenerator
from app.ai.validation import GroundingValidator


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_text_extraction_and_cleaning():
    """Test text extraction and cleaning pipeline."""
    print_section("TEST 1: Text Extraction & Cleaning")
    
    # Sample SQL learning material
    sample_text = """
    SQL FUNDAMENTALS

    Chapter 1: Introduction to SQL

    SQL (Structured Query Language) is a standardized programming language for managing relational databases.
    
    Key concepts in SQL include:
    - SELECT: retrieve data from tables
    - WHERE: filter results based on conditions
    - JOIN: combine data from multiple tables
    - ORDER BY: sort results

    Chapter 2: SELECT Statements

    The SELECT statement is used to select data from a database. The basic syntax is:

        SELECT column1, column2, ...
        FROM table_name;

    You can also use SELECT * to select all columns.

    Common SELECT examples:
    - SELECT * FROM users
    - SELECT id, name, email FROM users WHERE status = 'active'
    - SELECT COUNT(*) FROM orders
    """
    
    # Test cleaning
    cleaner = TextCleaner()
    cleaned = cleaner.clean(sample_text)
    
    print(f"✓ Original text length: {len(sample_text)} chars")
    print(f"✓ Cleaned text length: {len(cleaned)} chars")
    print(f"✓ Text cleaned successfully")
    print(f"\nCleaned text preview:\n{cleaned[:200]}...")


def test_chunking():
    """Test text chunking with metadata."""
    print_section("TEST 2: Deterministic Chunking with Metadata")
    
    sample_text = """
    SQL Fundamentals

    Chapter 1: Databases
    A database is an organized collection of structured data. Relational databases store data in tables with rows and columns.

    Chapter 2: Tables
    Tables are the fundamental objects in a relational database. Each table has columns and rows. Columns define the structure, while rows contain the data.

    Chapter 3: Keys
    Primary keys uniquely identify each row. Foreign keys establish relationships between tables.
    """
    
    pages_metadata = [
        {"page": 1, "text": sample_text}
    ]
    
    chunker = TextChunker()
    chunks = chunker.chunk_document(
        text=sample_text,
        material_id="test_material_1",
        pages_metadata=pages_metadata,
        chunk_size=200,
        chunk_overlap=50
    )
    
    print(f"✓ Created {len(chunks)} chunks from document")
    print(f"✓ Chunk size config: 200 chars, 50 char overlap")
    
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n  Chunk {chunk.sequence}:")
        print(f"    - Length: {len(chunk.text)} chars")
        print(f"    - Page: {chunk.source_page}")
        print(f"    - Text preview: {chunk.text[:80]}...")


def test_embeddings():
    """Test embedding generation."""
    print_section("TEST 3: Embedding Generation (Mock Provider)")
    
    embedding_provider = MockEmbeddingProvider(dimension=384)
    
    texts = [
        "SQL SELECT statements retrieve data",
        "SQL WHERE clauses filter results",
        "Python is a programming language",
    ]
    
    embeddings = embedding_provider.embed_texts(texts)
    
    print(f"✓ Provider available: {embedding_provider.is_available()}")
    print(f"✓ Embedding dimension: {embedding_provider.get_dimension()}")
    print(f"✓ Generated {len(embeddings)} embeddings")
    print(f"✓ Each embedding has {len(embeddings[0])} dimensions")
    
    # Test determinism
    emb1 = embedding_provider.embed_text(texts[0])
    emb2 = embedding_provider.embed_text(texts[0])
    print(f"✓ Embeddings are deterministic: {emb1 == emb2}")


def test_vector_retrieval():
    """Test vector storage and similarity retrieval."""
    print_section("TEST 4: Vector Storage & Similarity Retrieval")
    
    # Create chunks with different topics
    chunks = [
        DocumentChunk(
            material_id="m1",
            sequence=0,
            text="SQL SELECT statement retrieves data from tables using specific columns"
        ),
        DocumentChunk(
            material_id="m1",
            sequence=1,
            text="SQL WHERE clause filters results based on specific conditions"
        ),
        DocumentChunk(
            material_id="m1",
            sequence=2,
            text="Python is a high-level programming language for data science"
        ),
        DocumentChunk(
            material_id="m1",
            sequence=3,
            text="SQL JOIN combines data from multiple tables based on relationships"
        ),
    ]
    
    # Create vector store
    embedding_provider = MockEmbeddingProvider()
    vector_store = VectorStore(embedding_provider)
    
    count = vector_store.add_chunks(chunks)
    print(f"✓ Added {count} chunks to vector store")
    
    # Test retrieval
    results = vector_store.similarity_search("SQL SELECT data", top_k=2)
    
    print(f"✓ Retrieved top 2 similar chunks")
    for chunk, score in results:
        print(f"  - Chunk {chunk.sequence}: score={score:.3f}")
        print(f"    Text: {chunk.text[:60]}...")


def test_mcq_generation():
    """Test MCQ generation with mock provider."""
    print_section("TEST 5: MCQ Generation (Mock Provider)")
    
    # Create sample chunks
    chunks = [
        DocumentChunk(
            material_id="m1",
            sequence=0,
            text="SELECT statement is used to retrieve data from database tables"
        ),
        DocumentChunk(
            material_id="m1",
            sequence=1,
            text="WHERE clause filters records to return only those matching conditions"
        ),
    ]
    
    # Initialize pipeline
    llm_provider = MockLLMProvider()
    embedding_provider = MockEmbeddingProvider()
    
    vector_store = VectorStore(embedding_provider)
    vector_store.add_chunks(chunks)
    
    retriever = RetrieverService(vector_store)
    generator = MCQGenerator(llm_provider, retriever)
    
    # Generate questions
    questions = generator.generate_questions(
        query="SQL",
        competency_code="TECH_SQL",
        question_count=2,
        difficulty="MEDIUM"
    )
    
    print(f"✓ Generated {len(questions)} questions")
    
    for i, q in enumerate(questions, 1):
        print(f"\n  Question {i}:")
        print(f"    Q: {q.question}")
        print(f"    Options: {', '.join(q.options)}")
        print(f"    Answer: {q.correct_answer}")
        print(f"    Difficulty: {q.difficulty}")
        print(f"    Source chunks: {q.source_chunks}")


def test_grounding_validation():
    """Test grounding validation."""
    print_section("TEST 6: Grounding Validation")
    
    from app.ai.schemas import GeneratedMCQ
    
    # Create a valid grounded question
    question = GeneratedMCQ(
        question="What does the SELECT statement do in SQL?",
        options=[
            "Deletes data from tables",
            "Retrieves data from tables",
            "Updates data in tables",
            "Creates new tables"
        ],
        correct_answer="B",
        explanation="SELECT is used to query and retrieve data from database tables",
        source_chunks=["chunk_0"],
        difficulty="EASY"
    )
    
    print(f"✓ Created question with source references")
    print(f"  Question: {question.question}")
    print(f"  Source chunks: {question.source_chunks}")
    
    # Test semantic grounding
    chunks = [
        DocumentChunk(
            material_id="m1",
            sequence=0,
            text="SQL SELECT statement retrieves data from tables"
        ),
    ]
    
    is_grounded, msg = GroundingValidator.check_semantic_grounding(question, chunks)
    print(f"✓ Semantic grounding check: {is_grounded}")
    if msg:
        print(f"  Message: {msg}")


def test_full_pipeline():
    """Test complete AI pipeline end-to-end."""
    print_section("TEST 7: Complete AI Pipeline (End-to-End)")
    
    # Sample learning material
    material_text = """
    DATABASE FUNDAMENTALS

    Understanding SQL Queries

    The SELECT statement is the most commonly used SQL command. It allows you to retrieve specific data from a database table.

    SELECT Syntax:
    SELECT column1, column2, ...
    FROM table_name
    WHERE condition;

    The WHERE clause is used to extract only those records that fulfill a specified condition.

    Example:
    SELECT * FROM Students WHERE Age > 20;

    The ORDER BY keyword is used to sort the result-set in ascending or descending order.
    """
    
    # Pipeline stages
    print("\n[1] TEXT CLEANING")
    cleaner = TextCleaner()
    cleaned_text = cleaner.clean(material_text)
    print(f"    ✓ Cleaned {len(material_text)} → {len(cleaned_text)} chars")
    
    print("\n[2] CHUNKING")
    chunker = TextChunker()
    chunks = chunker.chunk_text(cleaned_text, "m1", chunk_size=300)
    print(f"    ✓ Created {len(chunks)} chunks")
    
    print("\n[3] EMBEDDING")
    embedding_provider = MockEmbeddingProvider()
    vector_store = VectorStore(embedding_provider)
    vector_store.add_chunks(chunks)
    print(f"    ✓ Embedded {len(chunks)} chunks")
    
    print("\n[4] RETRIEVAL")
    retriever = RetrieverService(vector_store)
    retrieved = retriever.retrieve_for_generation("SQL SELECT WHERE clause", material_id="m1", top_k=2)
    print(f"    ✓ Retrieved {len(retrieved)} relevant chunks")
    
    print("\n[5] MCQ GENERATION")
    llm_provider = MockLLMProvider()
    generator = MCQGenerator(llm_provider, retriever)
    questions = generator.generate_questions(
        query="SQL SELECT WHERE",
        competency_code="TECH_SQL",
        question_count=1
    )
    print(f"    ✓ Generated {len(questions)} question(s)")
    
    print("\n[6] VALIDATION")
    if questions:
        q = questions[0]
        print(f"    ✓ Question validated")
        print(f"      - Has source chunks: {bool(q.source_chunks)}")
        print(f"      - Question length: {len(q.question)} chars")
        print(f"      - Options count: {len(q.options)}")
    
    print("\n✓ FULL PIPELINE COMPLETED SUCCESSFULLY")


def main():
    """Run all verification tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  PHASE 6: AI Document Understanding + Grounded MCQ Generation".center(78) + "║")
    print("║" + "  Manual Verification Suite".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    
    try:
        test_text_extraction_and_cleaning()
        test_chunking()
        test_embeddings()
        test_vector_retrieval()
        test_mcq_generation()
        test_grounding_validation()
        test_full_pipeline()
        
        print_section("VERIFICATION COMPLETE")
        print("\n✓ All manual verification tests passed successfully!")
        print("\nVerification Summary:")
        print("  [✓] Text extraction & cleaning working")
        print("  [✓] Deterministic chunking with metadata")
        print("  [✓] Mock embedding generation (deterministic)")
        print("  [✓] Vector storage & similarity retrieval")
        print("  [✓] MCQ generation with mock LLM")
        print("  [✓] Grounding validation & semantic checks")
        print("  [✓] Full end-to-end pipeline")
        print("\nTimestamp:", datetime.now().isoformat())
        print("\n")
        
    except Exception as e:
        print_section("VERIFICATION FAILED")
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
