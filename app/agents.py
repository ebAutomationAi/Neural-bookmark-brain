from groq import AsyncGroq
from typing import Dict, List, Optional, Tuple
from loguru import logger
import json
import re
from datetime import datetime

from app.config import get_settings
from app.services.scraper import scraper
from app.services.classifier import classifier
from app.services.embeddings import get_embedding_service

settings = get_settings()


class ArchivistAgent:
    """
    Agente 1: El Archivista (The Gatekeeper)
    
    Responsabilidades:
    - Validar URLs
    - Scraping con Trafilatura
    - Clasificación de seguridad (NSFW)
    - Limpieza de títulos genéricos
    - Detección de URLs locales
    """
    
    def __init__(self):
        self.name = "Archivist"
        self.groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.embedding_service = get_embedding_service()
    
    async def process(self, url: str, original_title: str) -> Dict:
        """
        Procesa un bookmark a través del Agente Archivista
        
        Returns:
            Dict con: clean_title, full_text, is_nsfw, is_local, domain, etc.
        """
        logger.info(f"[{self.name}] Procesando: {url}")
        
        result = {
            "success": False,
            "clean_title": original_title,
            "full_text": None,
            "is_nsfw": False,
            "nsfw_reason": None,
            "is_local": False,
            "domain": None,
            "language": None,
            "word_count": 0,
            "error": None,
        }
        
        try:
            # 1. Scraping del contenido
            scraped = await scraper.scrape_url(url)
            
            result["domain"] = scraped.get("domain")
            result["language"] = scraped.get("language")
            result["word_count"] = scraped.get("word_count", 0)
            
            # Si es URL local
            if "local" in scraped.get("error", "").lower():
                result["is_local"] = True
                result["error"] = scraped["error"]
                logger.warning(f"[{self.name}] URL local detectada: {url}")
                return result
            
            # Si scraping falló
            if not scraped["success"]:
                result["error"] = scraped.get("error", "Error desconocido en scraping")
                logger.error(f"[{self.name}] Scraping fallido: {result['error']}")
                return result
            
            # 2. Obtener texto limpio
            full_text = scraped.get("text", "")
            result["full_text"] = full_text
            
            # 3. Limpiar título genérico
            scraped_title = scraped.get("title", original_title)
            clean_title = scraper.extract_clean_title(
                scraped_title or original_title,
                result["domain"]
            )
            result["clean_title"] = clean_title
            
            # 4. Clasificación de seguridad (NSFW)
            is_nsfw, nsfw_reason = classifier.classify(
                url=url,
                title=clean_title,
                text=full_text
            )
            
            result["is_nsfw"] = is_nsfw
            result["nsfw_reason"] = nsfw_reason
            
            if is_nsfw:
                logger.warning(
                    f"[{self.name}] Contenido NSFW detectado: {url} "
                    f"(Razón: {nsfw_reason})"
                )
            
            # 5. Si el título sigue siendo genérico, mejorar con AI
            if self._is_generic_title(clean_title) and full_text:
                logger.info(f"[{self.name}] Mejorando título genérico con AI")
                enhanced_title = await self._enhance_title_with_ai(
                    clean_title, full_text[:1000]
                )
                if enhanced_title:
                    result["clean_title"] = enhanced_title
            
            result["success"] = True
            logger.info(
                f"[{self.name}] ✓ Procesamiento exitoso: {url} "
                f"({result['word_count']} palabras)"
            )
        
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"[{self.name}] Error procesando {url}: {e}")
        
        return result
    
    def _is_generic_title(self, title: str) -> bool:
        """Verifica si el título sigue siendo genérico"""
        generic_patterns = [
            r"página principal",
            r"main page",
            r"home",
            r"index",
            r"welcome",
            r"^[a-z0-9\-]+\.(com|net|org)",  # Solo dominio
        ]
        
        title_lower = title.lower()
        
        for pattern in generic_patterns:
            if re.search(pattern, title_lower):
                return True
        
        return False
    
    async def _enhance_title_with_ai(
        self,
        original_title: str,
        text_sample: str
    ) -> Optional[str]:
        """Mejora el título usando AI si es genérico"""
        try:
            prompt = f"""Analiza el siguiente contenido web y genera un título descriptivo y conciso (máximo 60 caracteres).

Título original: {original_title}

Contenido:
{text_sample}

Responde SOLO con el nuevo título, nada más."""

            response = await self.groq_client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=100,
            )
            
            enhanced_title = response.choices[0].message.content.strip()
            
            # Validar que no sea muy largo
            if len(enhanced_title) > 100:
                enhanced_title = enhanced_title[:97] + "..."
            
            logger.info(f"[{self.name}] Título mejorado: {enhanced_title}")
            return enhanced_title
        
        except Exception as e:
            logger.error(f"[{self.name}] Error mejorando título con AI: {e}")
            return None


class CuratorAgent:
    """
    Agente 2: El Curador (The Librarian)
    
    Responsabilidades:
    - Generar resumen (3 oraciones)
    - Crear tags temáticos
    - Asignar categoría
    - Generar embeddings semánticos
    """
    
    def __init__(self):
        self.name = "Curator"
        self.groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.embedding_service = get_embedding_service()
    
    async def process(
        self,
        clean_title: str,
        full_text: str,
        url: str
    ) -> Dict:
        """
        Procesa contenido a través del Agente Curador
        
        Returns:
            Dict con: summary, tags, category, embedding
        """
        logger.info(f"[{self.name}] Curando contenido de: {url}")
        
        result = {
            "success": False,
            "summary": None,
            "tags": [],
            "category": None,
            "embedding": None,
            "error": None,
        }
        
        try:
            # Si no hay texto, no podemos curar
            if not full_text or len(full_text.strip()) < 50:
                result["error"] = "Texto insuficiente para curación"
                logger.warning(f"[{self.name}] Texto insuficiente: {url}")
                return result
            
            # 1. Generar análisis con AI (summary, tags, category)
            ai_analysis = await self._analyze_with_ai(clean_title, full_text)
            
            if ai_analysis:
                result["summary"] = ai_analysis.get("summary")
                result["tags"] = ai_analysis.get("tags", [])
                result["category"] = ai_analysis.get("category")
            else:
                result["error"] = "Error en análisis AI"
                return result
            
            # 2. Generar embedding semántico
            # Combinar título + resumen para mejor contexto
            text_for_embedding = f"{clean_title}. {result['summary']}"
            
            embedding = self.embedding_service.generate_embedding(text_for_embedding)
            result["embedding"] = embedding
            
            result["success"] = True
            logger.info(
                f"[{self.name}] ✓ Curación exitosa: {url} "
                f"(Categoría: {result['category']}, Tags: {len(result['tags'])})"
            )
        
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"[{self.name}] Error curando {url}: {e}")
        
        return result
    
    async def _analyze_with_ai(
        self,
        title: str,
        text: str
    ) -> Optional[Dict]:
        """Analiza contenido con AI para extraer metadata semántica"""
        try:
            # Truncar texto para no exceder límites
            text_truncated = text[:3000]
            
            prompt = f"""Analiza el siguiente contenido web y genera metadata estructurada.

Título: {title}

Contenido:
{text_truncated}

Responde en formato JSON con esta estructura exacta:
{{
  "summary": "Resumen de exactamente 3 oraciones que capture la esencia del contenido",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "category": "una categoría principal"
}}

Categorías válidas: Tecnología, Negocios, Educación, Entretenimiento, Salud, Ciencia, Arte, Deportes, Noticias, Programación, Diseño, Marketing, Finanzas, Productividad, Otros

Tags: Genera 5-7 tags relevantes, específicos y descriptivos.

Responde SOLO con el JSON, sin explicaciones adicionales."""

            response = await self.groq_client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=settings.GROQ_TEMPERATURE,
                max_tokens=settings.GROQ_MAX_TOKENS,
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extraer JSON del contenido
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                analysis = json.loads(json_str)
                
                # Validar estructura
                if all(key in analysis for key in ["summary", "tags", "category"]):
                    # Limpiar tags (lowercase, sin duplicados)
                    analysis["tags"] = list(set(
                        tag.lower().strip() for tag in analysis["tags"]
                    ))
                    
                    logger.info(f"[{self.name}] Análisis AI completado")
                    return analysis
            
            logger.error(f"[{self.name}] JSON inválido en respuesta AI")
            return None
        
        except json.JSONDecodeError as e:
            logger.error(f"[{self.name}] Error parseando JSON: {e}")
            return None
        
        except Exception as e:
            logger.error(f"[{self.name}] Error en análisis AI: {e}")
            return None


class AgentOrchestrator:
    """
    Orquestador de Agentes
    
    Coordina el flujo de procesamiento entre Archivista y Curador
    """
    
    def __init__(self):
        self.archivist = ArchivistAgent()
        self.curator = CuratorAgent()
    
    async def process_bookmark(
        self,
        url: str,
        original_title: str
    ) -> Dict:
        """
        Procesa un bookmark completo a través de ambos agentes
        
        Returns:
            Dict completo con todos los campos procesados
        """
        start_time = datetime.now()
        
        logger.info(f"[Orchestrator] Iniciando procesamiento: {url}")
        
        result = {
            "success": False,
            "url": url,
            "original_title": original_title,
            "clean_title": original_title,
            "summary": None,
            "full_text": None,
            "tags": [],
            "category": None,
            "is_nsfw": False,
            "nsfw_reason": None,
            "is_local": False,
            "domain": None,
            "language": None,
            "word_count": 0,
            "embedding": None,
            "status": "failed",
            "error": None,
            "processing_time": 0,
        }
        
        try:
            # FASE 1: Agente Archivista
            archivist_result = await self.archivist.process(url, original_title)
            
            # Actualizar resultado
            result.update({
                "clean_title": archivist_result.get("clean_title", original_title),
                "full_text": archivist_result.get("full_text"),
                "is_nsfw": archivist_result.get("is_nsfw", False),
                "nsfw_reason": archivist_result.get("nsfw_reason"),
                "is_local": archivist_result.get("is_local", False),
                "domain": archivist_result.get("domain"),
                "language": archivist_result.get("language"),
                "word_count": archivist_result.get("word_count", 0),
            })
            
            # Si es local o falló, marcar para manual
            if result["is_local"]:
                result["status"] = "manual_required"
                result["error"] = archivist_result.get("error")
                logger.warning(f"[Orchestrator] URL local - Manual requerido: {url}")
                return result
            
            if not archivist_result["success"]:
                result["status"] = "failed"
                result["error"] = archivist_result.get("error")
                logger.error(f"[Orchestrator] Archivista falló: {url}")
                return result
            
            # FASE 2: Agente Curador (solo si hay texto suficiente)
            if result["full_text"] and len(result["full_text"]) >= 50:
                curator_result = await self.curator.process(
                    result["clean_title"],
                    result["full_text"],
                    url
                )
                
                if curator_result["success"]:
                    result.update({
                        "summary": curator_result.get("summary"),
                        "tags": curator_result.get("tags", []),
                        "category": curator_result.get("category"),
                        "embedding": curator_result.get("embedding"),
                    })
                    
                    result["status"] = "completed"
                    result["success"] = True
                else:
                    result["status"] = "failed"
                    result["error"] = curator_result.get("error")
                    logger.error(f"[Orchestrator] Curador falló: {url}")
            else:
                result["status"] = "failed"
                result["error"] = "Texto insuficiente para curación"
                logger.warning(f"[Orchestrator] Texto insuficiente: {url}")
        
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            logger.error(f"[Orchestrator] Error general: {e}")
        
        finally:
            # Calcular tiempo de procesamiento
            end_time = datetime.now()
            result["processing_time"] = (end_time - start_time).total_seconds()
            
            logger.info(
                f"[Orchestrator] Procesamiento completado: {url} "
                f"(Status: {result['status']}, Tiempo: {result['processing_time']:.2f}s)"
            )
        
        return result


# Singleton
orchestrator = AgentOrchestrator()
