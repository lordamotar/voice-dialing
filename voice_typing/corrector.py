import logging
from typing import Optional

logger = logging.getLogger(__name__)

class GrammarCorrector:
    def __init__(self, enable: bool, language: str):
        self.enable = enable
        self.language = language
        self.tool = None
        self.java_available = False

        if not self.enable:
            logger.info("Коррекция грамматики отключена в конфигурации.")
            return

        # Map language code for LanguageTool
        lt_lang = "ru-RU"
        if language == "kz":
            lt_lang = "kk-KZ"

        try:
            logger.info(f"Инициализация LanguageTool для языка '{lt_lang}'...")
            import language_tool_python
            
            # This might download the server jar if it's the first time
            # and starts a local Java server process
            self.tool = language_tool_python.LanguageTool(lt_lang)
            self.java_available = True
            logger.info("LanguageTool успешно инициализирован.")
        except Exception as e:
            self.tool = None
            self.java_available = False
            error_msg = str(e)
            
            logger.warning(
                "Не удалось запустить LanguageTool. Коррекция грамматики будет пропущена.\n"
                f"Детали ошибки: {error_msg}\n"
                "ВОЗМОЖНАЯ ПРИЧИНА: Для работы LanguageTool требуется установленная Java (JRE/JDK).\n"
                "Пожалуйста, установите Java и добавьте её в переменную окружения PATH.\n"
                "Ссылка для скачивания Java JRE: https://www.java.com/ru/download/"
            )
            print(
                "\n[ПРЕДУПРЕЖДЕНИЕ] LanguageTool (корректор) не запущен, так как не найдена Java (или произошла ошибка).\n"
                "Распознанный текст будет печататься без автоматического исправления грамматики.\n"
            )

    def correct(self, text: str) -> str:
        """Correct grammar, capitalize first letter, and apply basic punctuation heuristics."""
        if not text:
            return ""

        corrected = text.strip()

        # 1. Apply LanguageTool correction if available
        if self.enable and self.java_available and self.tool:
            try:
                logger.debug(f"Исходный текст для коррекции: '{corrected}'")
                corrected = self.tool.correct(corrected)
                logger.debug(f"Текст после LanguageTool: '{corrected}'")
            except Exception as e:
                logger.error(f"Ошибка при работе LanguageTool: {e}")

        # 2. Heuristics fallback/post-processing
        if corrected:
            # Capitalize first letter
            corrected = corrected[0].upper() + corrected[1:]
            
            # Ensure basic trailing punctuation if missing
            punctuation_marks = (".", "?", "!", ",", ";", ":", "-")
            if not corrected.endswith(punctuation_marks):
                corrected += "."

        return corrected

    def close(self):
        """Clean up the local language tool server if it was started."""
        if self.tool:
            try:
                self.tool.close()
            except Exception as e:
                logger.debug(f"Ошибка при закрытии LanguageTool: {e}")
