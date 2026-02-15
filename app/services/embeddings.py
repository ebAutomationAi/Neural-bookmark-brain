from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
from loguru import logger
from functools import lru_cache

from app.config import get_settings

settings = get_settings()


class EmbeddingService:
    """Servicio de generación de embeddings semánticos"""
    
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        self._model = None
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy loading del modelo"""
        if self._model is None:
            try:
                logger.info(f"Cargando modelo de embeddings: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Modelo cargado exitosamente")
            except Exception as e:
                print(f"Error cargando modelo de embeddings: {e}")
                logger.error(f"Error cargando modelo de embeddings: {e}")
                raise
        return self._model
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Genera embedding para un texto
        
        Args:
            text: Texto a vectorizar
        
        Returns:
            Lista de floats (embedding vector)
        """
        if not text or not text.strip():
            logger.warning("Texto vacío para embedding, retornando vector cero")
            return [0.0] * self.dimension
        
        try:
            # Truncar texto si es muy largo (max 512 tokens)
            text_truncated = text[:2000]
            
            # Generar embedding
            embedding = self.model.encode(
                text_truncated,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            # Convertir a lista
            embedding_list = embedding.tolist()
            
            # Normalizar (opcional pero recomendado para cosine similarity)
            embedding_normalized = self._normalize(embedding_list)
            
            logger.debug(f"Embedding generado para texto de {len(text)} chars")
            
            return embedding_normalized
        
        except Exception as e:
            print(f"Error generando embedding: {e}")
            logger.error(f"Error generando embedding: {e}")
            return [0.0] * self.dimension
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Genera embedding optimizado para queries de búsqueda
        
        Args:
            query: Query de búsqueda
        
        Returns:
            Embedding vector
        """
        # Para queries, podemos preprocesar el texto
        query_clean = query.strip().lower()
        
        return self.generate_embedding(query_clean)
    
    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Genera embeddings para múltiples textos (más eficiente)
        
        Args:
            texts: Lista de textos
        
        Returns:
            Lista de embeddings
        """
        if not texts:
            return []
        
        try:
            # Truncar textos
            texts_truncated = [text[:2000] if text else "" for text in texts]
            
            # Generar embeddings en batch
            embeddings = self.model.encode(
                texts_truncated,
                convert_to_numpy=True,
                show_progress_bar=True,
                batch_size=32
            )
            
            # Normalizar
            embeddings_normalized = [
                self._normalize(emb.tolist()) for emb in embeddings
            ]
            
            logger.info(f"Generados {len(embeddings_normalized)} embeddings en batch")
            
            return embeddings_normalized
        
        except Exception as e:
            print(f"Error generando batch embeddings: {e}")
            logger.error(f"Error generando batch embeddings: {e}")
            return [[0.0] * self.dimension] * len(texts)
    
    def _normalize(self, vector: List[float]) -> List[float]:
        """Normaliza un vector (L2 normalization)"""
        try:
            np_vector = np.array(vector)
            norm = np.linalg.norm(np_vector)
            
            if norm == 0:
                return vector
            
            normalized = (np_vector / norm).tolist()
            return normalized
        
        except Exception as e:
            print(f"Error normalizando vector: {e}")
            logger.error(f"Error normalizando vector: {e}")
            return vector
    
    def calculate_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calcula similitud coseno entre dos embeddings
        
        Args:
            embedding1: Primer embedding
            embedding2: Segundo embedding
        
        Returns:
            Score de similitud [0, 1]
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Cosine similarity
            similarity = np.dot(vec1, vec2) / (
                np.linalg.norm(vec1) * np.linalg.norm(vec2)
            )
            
            # Convertir de [-1, 1] a [0, 1]
            similarity_normalized = (similarity + 1) / 2
            
            return float(similarity_normalized)
        
        except Exception as e:
            print(f"Error calculando similitud: {e}")
            logger.error(f"Error calculando similitud: {e}")
            return 0.0


# Singleton
@lru_cache()
def get_embedding_service() -> EmbeddingService:
    """Obtiene instancia singleton del servicio de embeddings"""
    return EmbeddingService()
