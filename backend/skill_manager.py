"""
Skill Manager for Keywords Checker
Loads skill definitions and reference files from the skills directory
"""

import os
import re
import logging
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


class SkillManager:
    """Manages loading and retrieval of skill definitions"""
    
    def __init__(self, skills_dir):
        """
        Initialize the SkillManager
        
        Args:
            skills_dir: Path to the skills directory
        """
        self.skills_dir = Path(skills_dir)
        self.skills = {}
        
    def load_all_skills(self):
        """Load all skills from the skills directory"""
        if not self.skills_dir.exists():
            raise FileNotFoundError(f"Skills directory not found: {self.skills_dir}")
            
        # Look for skill directories
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    skill_data = self.load_skill_file(skill_file)
                    if skill_data:
                        self.skills[skill_data['name']] = skill_data
                        
        return self.skills
    
    def load_skill_file(self, skill_file_path):
        """
        Load a single SKILL.md file
        
        Args:
            skill_file_path: Path to the SKILL.md file
            
        Returns:
            Dictionary containing skill data with name, description, content, and references
        """
        try:
            with open(skill_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse YAML frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    markdown_content = parts[2].strip()
                else:
                    frontmatter = {}
                    markdown_content = content
            else:
                frontmatter = {}
                markdown_content = content
            
            # Load references
            skill_dir = skill_file_path.parent
            references = self.load_references(skill_dir)
            
            skill_data = {
                'name': frontmatter.get('name', skill_dir.name),
                'description': frontmatter.get('description', ''),
                'content': markdown_content,
                'references': references,
                'path': skill_dir
            }
            
            return skill_data
            
        except Exception as e:
            logger.error(f"Error loading skill file {skill_file_path}: {e}", exc_info=True)
            return None
    
    def load_references(self, skill_dir):
        """
        Load all reference files from the references directory
        
        Args:
            skill_dir: Path to the skill directory
            
        Returns:
            Dictionary mapping reference names to their content
        """
        references = {}
        references_dir = skill_dir / "references"
        
        if not references_dir.exists():
            return references
        
        for ref_file in references_dir.glob("*.md"):
            try:
                with open(ref_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Use filename without extension as key
                    ref_name = ref_file.stem
                    references[ref_name] = content
            except Exception as e:
                logger.error(f"Error loading reference file {ref_file}: {e}", exc_info=True)
        
        return references
    
    def build_system_prompt(self, skill_name):
        """
        Build a system prompt for the LLM including skill definition and references
        
        Args:
            skill_name: Name of the skill to build prompt for
            
        Returns:
            String containing the complete system prompt
        """
        skill = self.skills.get(skill_name)
        if not skill:
            raise ValueError(f"Skill not found: {skill_name}")
        
        # Start with the main skill content
        prompt_parts = [skill['content']]
        
        # Add references if available
        if skill['references']:
            prompt_parts.append("\n\n## チェック用キーワード参照\n")
            
            # Add list of available keywords
            keyword_list = "以下のキーワードについてのルールが定義されています:\n"
            for ref_name in sorted(skill['references'].keys()):
                keyword_list += f"- {ref_name}\n"
            prompt_parts.append(keyword_list)
            
            # Add all reference content
            prompt_parts.append("\n## 各キーワードの詳細ルール\n")
            for ref_name, ref_content in sorted(skill['references'].items()):
                prompt_parts.append(f"\n### {ref_name}\n")
                prompt_parts.append(ref_content)
        
        return "\n".join(prompt_parts)
    
    def detect_keywords(self, skill_name, text):
        """
        Detect keywords from product text that exist in references
        Uses word boundary detection for more precise matching
        
        Args:
            skill_name: Name of the skill
            text: Product text to check for keywords
            
        Returns:
            List of detected keyword names
        """
        skill = self.skills.get(skill_name)
        if not skill or not skill['references']:
            return []
        
        detected = []
        
        # キーワード名（ファイル名）で単語境界を考慮した検索
        for keyword_name in skill['references'].keys():
            # キーワードを正規表現用にエスケープ
            escaped_keyword = re.escape(keyword_name)
            
            # 日本語と英語の両方に対応したパターン
            # 英語: \bで単語境界をチェック
            # 日本語: 前後が英数字でないことを確認
            patterns = [
                # 英語キーワード用（単語境界\bを使用）
                rf'\b{escaped_keyword}\b',
                # 日本語キーワード用（前後が英数字以外）
                rf'(?<![a-zA-Z0-9]){escaped_keyword}(?![a-zA-Z0-9])',
                # シンプルな部分一致（フォールバック）
                escaped_keyword
            ]
            
            # いずれかのパターンにマッチすれば検出
            for pattern in patterns:
                try:
                    if re.search(pattern, text, re.IGNORECASE):
                        detected.append(keyword_name)
                        break  # このキーワードは検出済み
                except re.error:
                    # 正規表現エラーの場合は次のパターンを試す
                    continue
        
        return detected
    
    def build_dynamic_system_prompt(self, skill_name, detected_keywords):
        """
        Build a system prompt with only detected keywords' references
        
        Args:
            skill_name: Name of the skill to build prompt for
            detected_keywords: List of detected keyword names
            
        Returns:
            String containing the system prompt with only relevant references
        """
        skill = self.skills.get(skill_name)
        if not skill:
            raise ValueError(f"Skill not found: {skill_name}")
        
        # Start with the main skill content
        prompt_parts = [skill['content']]
        
        # Add only detected keywords' references
        if detected_keywords and skill['references']:
            prompt_parts.append("\n\n## チェック用キーワード参照\n")
            
            # Add list of detected keywords
            keyword_list = "以下のキーワードが検出されました:\n"
            for keyword_name in sorted(detected_keywords):
                keyword_list += f"- {keyword_name}\n"
            prompt_parts.append(keyword_list)
            
            # Add only detected keywords' reference content
            prompt_parts.append("\n## 各キーワードの詳細ルール\n")
            for keyword_name in sorted(detected_keywords):
                if keyword_name in skill['references']:
                    prompt_parts.append(f"\n### {keyword_name}\n")
                    prompt_parts.append(skill['references'][keyword_name])
        else:
            # キーワードが検出されなかった場合の注記
            prompt_parts.append("\n\n## 注意\n")
            prompt_parts.append("商品テキストから該当するキーワードが検出されませんでしたが、一般的な薬機法・景表法の観点からチェックしてください。")
        
        return "\n".join(prompt_parts)
    
    def get_skill_by_name(self, skill_name):
        """Get a skill by name"""
        return self.skills.get(skill_name)
    
    def list_skills(self):
        """List all available skills"""
        return [
            {
                'name': skill['name'],
                'description': skill['description']
            }
            for skill in self.skills.values()
        ]
