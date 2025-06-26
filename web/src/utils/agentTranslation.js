import { useI18n } from 'vue-i18n';

/**
 * Utility function to translate agent descriptions
 * This helps override backend hardcoded Chinese descriptions with i18n translations
 */
export function useAgentTranslation() {
  const { t } = useI18n();

  /**
   * Translate agent description, falling back to original if no translation exists
   * @param {Object} agent - Agent object with name and description
   * @returns {string} - Translated description or original description
   */
  const translateAgentDescription = (agent) => {
    if (!agent) return '';
    
    // Check if we have a translation for this agent's description
    const translationKey = `agents.descriptions.${agent.name}`;
    const translatedDescription = t(translationKey);
    
    // If translation exists and is different from the key, use it
    if (translatedDescription && translatedDescription !== translationKey) {
      return translatedDescription;
    }
    
    // Otherwise, fall back to the original description
    return agent.description || '';
  };

  return {
    translateAgentDescription
  };
} 