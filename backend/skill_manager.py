"""
Skill Manager for Keywords Checker
Loads skill definitions and reference files from the skills directory
"""

import os
import yaml
from pathlib import Path


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
            print(f"Error loading skill file {skill_file_path}: {e}")
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
                print(f"Error loading reference file {ref_file}: {e}")
        
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
