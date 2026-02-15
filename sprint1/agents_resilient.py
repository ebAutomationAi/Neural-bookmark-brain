# app/agents.py - VERSIÓN CON RESILIENCIA Y ESTADOS PARCIALES

from groq import AsyncGroq
from typing import Dict, List, Optional, Tuple
from loguru import logger
import json
import re
from datetime import datetime
from urllib.parse import urlparse
import tldextract

from app.config import get_settings
from app.services.scraper import scraper
from app.services.classifier import classifier
from app.services.embeddings import get_embedding_service

settings = get_settings()


class ArchivistAgent:
    """
    Agente 1: El Archivista (The Gatekeeper) - VERSIÓN RESILIENTE
    
    Responsabilidades:
    - Validar URLs
    - Scraping resiliente con múltiples estrategias
    - Clasificación de seguridad (NSFW)
    - Limpieza de títulos genéricos
    - Detección de URLs locales
    - Clasificación de errores
    """
    
    def __init__(self):
        self.name = "Archivist"
        self.groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.embedding_service = get_embedding_service()
    
    async def process(self, url: str, original_title: str) -> Dict:
        """
        Procesa un bookmark a través del Agente Archivista
        
        Returns:
            Dict con: clean_title, full_text, is_nsfw, scraping_status, error_type, etc.
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
            # Nuevos campos de resiliencia
            "scraping_status": "pending",
            "scraping_strategy": None,
            "scraping_error_type": None,
            "scraping_attempts": 0,
        }
        
        try:
            # 1. Scraping del contenido con estrategias resilientes
            scraped = await scraper.scrape_url(url)
            
            result["domain"] = scraped.get("domain")
            result["language"] = scraped.get("language")
            result["word_count"] = scraped.get("word_count", 0)
            result["scraping_strategy"] = scraped.get("strategy")
            result["scraping_error_type"] = scraped.get("error_type")
            result["scraping_attempts"] = scraped.get("attempts", 0)
            
            # Si es URL local
            if scraped.get("error_type") == "local_url":
                result["is_local"] = True
                result["scraping_status"] = "skipped"
                result["error"] = scraped["error_message"]
                logger.warning(f"[{self.name}] URL local detectada: {url}")
                return result
            
            # Si scraping fue exitoso
            if scraped["success"]:
                result["scraping_status"] = "success"
                result["full_text"] = scraped.get("text", "")
                
                # 2. Obtener título limpio
                scraped_title = scraped.get("title", original_title)
                clean_title = scraper.extract_clean_title(
                    scraped_title or original_title,
                    result["domain"]
                )
                result["clean_title"] = clean_title
                
                # 3. Clasificación de seguridad (NSFW)
                is_nsfw, nsfw_reason = classifier.classify(
                    url=url,
                    title=clean_title,
                    text=result["full_text"]
                )
                
                result["is_nsfw"] = is_nsfw
                result["nsfw_reason"] = nsfw_reason
                
                if is_nsfw:
                    logger.warning(
                        f"[{self.name}] Contenido NSFW detectado: {url} "
                        f"(Razón: {nsfw_reason})"
                    )
                
                # 4. Si el título sigue siendo genérico, mejorar con AI
                if self._is_generic_title(clean_title) and result["full_text"]:
                    logger.info(f"[{self.name}] Mejorando título genérico con AI")
                    enhanced_title = await self._enhance_title_with_ai(
                        clean_title, result["full_text"][:1000]
                    )
                    if enhanced_title:
                        result["clean_title"] = enhanced_title
                
                result["success"] = True
                logger.info(
                    f"[{self.name}] ✅ Procesamiento exitoso: {url} "
                    f"({result['word_count']} palabras, estrategia: {result['scraping_strategy']})"
                )
            
            else:
                # Scraping falló pero tenemos metadata de error
                result["scraping_status"] = "failed"
                result["error"] = scraped.get("error_message", "Error desconocido en scraping")
                
                logger.warning(
                    f"[{self.name}] ⚠️ Scraping fallido: {url} "
                    f"(Tipo: {result['scraping_error_type']}, Intentos: {result['scraping_attempts']})"
                )
                
                # Aún así intentamos limpiar el título original
                result["clean_title"] = scraper.extract_clean_title(
                    original_title,
                    result["domain"]
                )
        
        except Exception as e:
            result["error"] = str(e)
            result["scraping_status"] = "failed"
            result["scraping_error_type"] = "unexpected_error"
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
                temperature=getattr(settings, 'GROQ_TEMPERATURE', 0.3),
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
    Agente 2: El Curador (The Librarian) - VERSIÓN CON MODO FALLBACK
    
    Responsabilidades:
    - Generar resumen (3 oraciones)
    - Crear tags temáticos
    - Asignar categoría
    - Generar embeddings semánticos
    - NUEVO: Modo fallback para URLs sin contenido
    """
    
    def __init__(self):
        self.name = "Curator"
        self.groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.embedding_service = get_embedding_service()
    
    async def process(
        self,
        clean_title: str,
        full_text: Optional[str],
        url: str
    ) -> Dict:
        """
        Procesa contenido a través del Agente Curador
        AUTOMÁTICAMENTE decide entre modo full_text o url_only
        
        Returns:
            Dict con: summary, tags, category, embedding, curation_mode, confidence
        """
        logger.info(f"[{self.name}] Curando contenido de: {url}")
        
        result = {
            "success": False,
            "summary": None,
            "tags": [],
            "category": None,
            "embedding": None,
            "error": None,
            "curation_status": "pending",
            "curation_mode": None,
            "confidence": 0.0,
        }
        
        try:
            # Decidir modo basado en disponibilidad de texto
            if full_text and len(full_text.strip()) >= 50:
                # MODO NORMAL: Texto completo disponible
                logger.info(f"[{self.name}] Modo: full_text ({len(full_text)} chars)")
                ai_result = await self._process_full_text(clean_title, full_text, url)
                result["curation_mode"] = "full_text"
                result["confidence"] = 1.0  # Alta confianza
            else:
                # MODO FALLBACK: Solo URL + título
                logger.warning(f"[{self.name}] Modo: url_only (texto insuficiente)")
                ai_result = await self._process_url_only(clean_title, url)
                result["curation_mode"] = "url_only"
                result["confidence"] = ai_result.get("confidence", 0.5)
            
            if ai_result and ai_result.get("success"):
                result["summary"] = ai_result.get("summary")
                result["tags"] = ai_result.get("tags", [])
                result["category"] = ai_result.get("category")
                
                # Generar embedding
                text_for_embedding = f"{clean_title}. {result['summary']}"
                embedding = self.embedding_service.generate_embedding(text_for_embedding)
                result["embedding"] = embedding
                
                result["success"] = True
                result["curation_status"] = "success" if result["curation_mode"] == "full_text" else "fallback"
                
                logger.info(
                    f"[{self.name}] ✅ Curación exitosa: {url} "
                    f"(Modo: {result['curation_mode']}, Categoría: {result['category']}, "
                    f"Confidence: {result['confidence']:.2f})"
                )
            else:
                result["error"] = ai_result.get("error", "Error en análisis AI")
                result["curation_status"] = "failed"
                logger.error(f"[{self.name}] Error en análisis AI: {url}")
        
        except Exception as e:
            result["error"] = str(e)
            result["curation_status"] = "failed"
            logger.error(f"[{self.name}] Error curando {url}: {e}")
        
        return result
    
    async def _process_full_text(
        self,
        title: str,
        text: str,
        url: str
    ) -> Optional[Dict]:
        """Modo normal: análisis con texto completo"""
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

Categorías válidas: Tecnología, Negocios, Educación, Entretenimiento, Salud, Ciencia, Arte, Deportes, Noticias, Programación, Diseño, Marketing, Finanzas, Productividad, Transporte, Otros

Tags: Genera 5-7 tags relevantes, específicos y descriptivos.

Responde SOLO con el JSON, sin explicaciones adicionales."""

            response = await self.groq_client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=getattr(settings, 'GROQ_TEMPERATURE', 0.3),
                max_tokens=getattr(settings, 'GROQ_MAX_TOKENS', 2048),
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
                    
                    analysis["success"] = True
                    logger.info(f"[{self.name}] Análisis AI completado (full_text)")
                    return analysis
            
            logger.error(f"[{self.name}] JSON inválido en respuesta AI")
            return {"success": False, "error": "JSON inválido"}
        
        except json.JSONDecodeError as e:
            logger.error(f"[{self.name}] Error parseando JSON: {e}")
            return {"success": False, "error": f"JSON parse error: {e}"}
        
        except Exception as e:
            logger.error(f"[{self.name}] Error en análisis AI: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_url_only(
        self,
        title: str,
        url: str
    ) -> Optional[Dict]:
        """
        MODO FALLBACK: Categorización solo con URL + título
        Usa análisis estructurado de la URL y conocimiento de dominios
        """
        try:
            # Analizar URL de forma estructurada
            domain_info = self._analyze_domain(url)
            path_info = self._analyze_path(url)
            
            prompt = f"""Analiza esta información limitada de un bookmark:

URL: {url}
Título original: {title}

Información del dominio:
- Dominio: {domain_info['domain']}
- TLD: {domain_info['tld']}
- Subdominios: {domain_info['subdomains']}

Información del path:
- Segmentos: {path_info['segments']}
- Keywords detectadas: {path_info['keywords']}

CONTEXTO IMPORTANTE: No pudimos acceder al contenido de la página (bloqueado, timeout o error).
Usa tu conocimiento previo sobre este dominio y los patrones en la URL para hacer una inferencia educada.

Genera metadata en formato JSON:
{{
  "summary": "Resumen de 2 oraciones sobre qué probablemente contiene esta página",
  "tags": ["tag1", "tag2", "tag3", "tag4"],
  "category": "una categoría principal",
  "confidence": 0.7
}}

Categorías válidas: Tecnología, Negocios, Educación, Entretenimiento, Salud, Ciencia, Arte, Deportes, Noticias, Programación, Diseño, Marketing, Finanzas, Productividad, Transporte, Otros

EJEMPLOS de buenas inferencias:
- URL "https://www.tmb.cat/es/horarios-metro" → Category: "Transporte", Tags: ["transporte público", "metro", "barcelona"], Confidence: 0.8
- URL "https://www.coursera.org/learn/machine-learning" → Category: "Educación", Tags: ["educación online", "machine learning"], Confidence: 0.9
- URL "https://github.com/user/awesome-python" → Category: "Programación", Tags: ["python", "github", "recursos"], Confidence: 0.9

Confidence:
- 0.9-1.0: Dominio muy conocido (google.com, github.com, wikipedia.org)
- 0.7-0.8: Dominio reconocible o path muy descriptivo
- 0.5-0.6: Dominio desconocido pero path informativo
- 0.3-0.4: Muy poca información disponible

Responde SOLO con el JSON."""

            response = await self.groq_client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,  # Más conservadora para inferencias
                max_tokens=500,
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parsear JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                analysis = json.loads(json_str)
                
                if all(key in analysis for key in ["summary", "tags", "category"]):
                    analysis["tags"] = list(set(
                        tag.lower().strip() for tag in analysis["tags"]
                    ))
                    analysis["success"] = True
                    
                    logger.info(
                        f"[{self.name}] Análisis AI completado (url_only) - "
                        f"Confidence: {analysis.get('confidence', 0.5):.2f}"
                    )
                    return analysis
            
            return {"success": False, "error": "JSON inválido"}
        
        except Exception as e:
            logger.error(f"[{self.name}] Error en análisis url_only: {e}")
            return {"success": False, "error": str(e)}
    
    def _analyze_domain(self, url: str) -> Dict:
        """Extrae información estructurada del dominio"""
        extracted = tldextract.extract(url)
        
        return {
            "domain": extracted.domain,
            "tld": extracted.suffix,
            "subdomains": extracted.subdomain.split('.') if extracted.subdomain else [],
            "full_domain": f"{extracted.domain}.{extracted.suffix}"
        }
    
    def _analyze_path(self, url: str) -> Dict:
        """Analiza el path de la URL para extraer keywords"""
        parsed = urlparse(url)
        segments = [s for s in parsed.path.split('/') if s]
        
        # Keywords comunes en URLs por categoría
        category_keywords = {
            'transporte': ['bus', 'metro', 'tren', 'transport', 'horario', 'schedule', 'tmb', 'renfe'],
            'educación': ['curso', 'clase', 'university', 'edu', 'learning', 'tutorial', 'coursera'],
            'programación': ['github', 'code', 'dev', 'api', 'docs', 'python', 'javascript'],
            'noticias': ['news', 'noticias', 'article', 'post', 'blog'],
        }
        
        found_keywords = []
        for segment in segments:
            segment_lower = segment.lower()
            for category, keywords in category_keywords.items():
                if any(kw in segment_lower for kw in keywords):
                    found_keywords.append(category)
                    break
        
        return {
            "segments": segments,
            "keywords": list(set(found_keywords))  # Sin duplicados
        }


class AgentOrchestrator:
    """
    Orquestador de Agentes - VERSIÓN CON ESTADOS PARCIALES
    
    Coordina el flujo de procesamiento entre Archivista y Curador
    Permite procesamiento parcial exitoso
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
        GARANTIZA que siempre se intenta la curación, incluso si scraping falla
        
        Returns:
            Dict completo con todos los campos procesados y estados parciales
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
            # Estados
            "status": "failed",
            "scraping_status": "pending",
            "scraping_strategy": None,
            "scraping_error_type": None,
            "scraping_attempts": 0,
            "curation_status": "pending",
            "curation_mode": None,
            "confidence_score": 0.0,
            # Metadata
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
                "scraping_status": archivist_result.get("scraping_status", "failed"),
                "scraping_strategy": archivist_result.get("scraping_strategy"),
                "scraping_error_type": archivist_result.get("scraping_error_type"),
                "scraping_attempts": archivist_result.get("scraping_attempts", 0),
            })
            
            # Si es local, marcar para manual
            if result["is_local"]:
                result["status"] = "manual_required"
                result["error"] = archivist_result.get("error")
                logger.warning(f"[Orchestrator] URL local - Manual requerido: {url}")
                return result
            
            # FASE 2: Agente Curador (SIEMPRE se ejecuta, incluso si scraping falló)
            curator_result = await self.curator.process(
                result["clean_title"],
                result["full_text"],  # Puede ser None
                url
            )
            
            if curator_result["success"]:
                result.update({
                    "summary": curator_result.get("summary"),
                    "tags": curator_result.get("tags", []),
                    "category": curator_result.get("category"),
                    "embedding": curator_result.get("embedding"),
                    "curation_status": curator_result.get("curation_status"),
                    "curation_mode": curator_result.get("curation_mode"),
                    "confidence_score": curator_result.get("confidence", 0.0),
                })
                
                # Determinar estado final
                if result["scraping_status"] == "success":
                    result["status"] = "completed"
                    result["success"] = True
                else:
                    # Scraping falló pero curación exitosa
                    result["status"] = "completed_partial"
                    result["success"] = True
                    result["error"] = archivist_result.get("error")
                
                logger.info(
                    f"[Orchestrator] ✅ Procesamiento exitoso: {url} "
                    f"(Status: {result['status']}, Confidence: {result['confidence_score']:.2f})"
                )
            else:
                # Tanto scraping como curación fallaron
                result["status"] = "failed"
                result["curation_status"] = "failed"
                result["error"] = curator_result.get("error") or archivist_result.get("error")
                logger.error(f"[Orchestrator] ❌ Procesamiento fallido: {url}")
        
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