const { hasSkillAccess, parseSkill } = require('../src/lib/skills');
const { resolveClueState, buildSkillLockedMessage } = require('../src/js/clue-access');

// Deterministic random function for testing (always picks first item)
function deterministicRandom(array) {
  return array[0];
}

// Mock no-access messages for all tests
const mockNoAccessMessages = {
  skill_phrases: {
    art: {
      level_1: ['artistic knowledge'],
      level_2: ['expert artistic knowledge']
    },
    medical: {
      level_1: ['medical training'],
      level_2: ['expert medical training']
    },
    botanical: {
      level_1: ['botanical knowledge'],
      level_2: ['expert botanical knowledge']
    }
  },
  wrappers: {
    'Artifact (Object)': ['You need {requirements} to understand this.'],
    'Document': ['This document requires {requirements} to decipher.'],
    '_default': ['The meaning here escapes you. You\'d need {requirements}.']
  }
};

describe('clue access state', () => {
  // Helper to simulate localStorage state
  function createAccessState(clueData, { userSkills = [] }) {
    return resolveClueState(clueData, {
      userSkills,
      noAccessMessages: mockNoAccessMessages,
      hasSkillAccessFn: hasSkillAccess,
      parseSkillFn: parseSkill,
      randomFn: deterministicRandom
    });
  }

  describe('skill requirements', () => {
    test('player cannot view clue when lacking required expertise', () => {
      const clueData = {
        id: 'CLUE123',
        act: 'act_i_setting',
        skills: ['art_2'],
        type: 'Artifact (Object)'
      };
      const state = createAccessState(clueData, {
        userSkills: ['art_1'] // Only level 1, needs level 2
      });

      expect(state.name).toBe('skill-locked');
      expect(state.message).toContain('artistic');
    });

    test('player can view clue when they have the required expertise', () => {
      const clueData = {
        id: 'CLUE123',
        act: 'act_i_setting',
        skills: ['art_2']
      };
      const state = createAccessState(clueData, {
        userSkills: ['art_2'] // Has required level
      });

      expect(state.name).toBe('unlocked');
    });

    test('player sees which characters can help with a skill-locked clue', () => {
      const clueData = {
        id: 'CLUE123',
        act: 'act_i_setting',
        skills: ['art_2'],
        accessChars: ['Alice', 'Bob']
      };
      const state = createAccessState(clueData, {
        userSkills: [] // No skills
      });

      expect(state.name).toBe('skill-locked');
      expect(state.suggestedCharacters).toEqual(['Alice', 'Bob']);
    });

    test('clues with no skill requirements are accessible to everyone', () => {
      const clueData = {
        id: 'CLUE123',
        act: 'act_i_setting',
        skills: []
      };
      const state = createAccessState(clueData, {
        userSkills: [] // No skills at all
      });

      expect(state.name).toBe('unlocked');
    });
  });
});

describe('skill-locked feedback', () => {
  test('player sees what expertise they need for a locked clue', () => {
    const message = buildSkillLockedMessage(
      ['art_1'],
      'Artifact (Object)',
      mockNoAccessMessages,
      parseSkill,
      deterministicRandom
    );

    expect(message).toBe('You need artistic knowledge to understand this.');
  });

  test('player sees what expertise they need at higher skill levels', () => {
    const message = buildSkillLockedMessage(
      ['art_2'],
      'Artifact (Object)',
      mockNoAccessMessages,
      parseSkill,
      deterministicRandom
    );

    expect(message).toBe('You need expert artistic knowledge to understand this.');
  });

  test('player sees multiple skill options when any would unlock the clue', () => {
    const message = buildSkillLockedMessage(
      ['art_1', 'medical_1'],
      'Document',
      mockNoAccessMessages,
      parseSkill,
      deterministicRandom
    );

    expect(message).toBe('This document requires artistic knowledge or medical training to decipher.');
  });

  test('player sees a generic message when skill descriptions are unavailable', () => {
    const message = buildSkillLockedMessage(
      ['unknown_skill_1'],
      'Artifact (Object)',
      mockNoAccessMessages,
      parseSkill,
      deterministicRandom
    );

    expect(message).toBe('You need the required expertise to understand this.');
  });
});
