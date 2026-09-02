from core.pipeline.rag_pipeline import RAGPipeline

rag = RAGPipeline()

query = "MRB是什麼"

result = rag.run(query)

print("\n==== FINAL ANSWER ====")
print(result["answer"])
