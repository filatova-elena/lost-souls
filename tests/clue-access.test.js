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
  function createAccessState(clueData, { unlockedActs = [], userSkills = [] }) {
    return resolveClueState(clueData, {
      unlockedActs,
      userSkills,
      noAccessMessages: mockNoAccessMessages,
      hasSkillAccessFn: hasSkillAccess,
      parseSkillFn: parseSkill,
      randomFn: deterministicRandom
    });
  }

  describe('story gate progression', () => {
    // Story-gate locking is currently DISABLED in clue-access.js (trying the
    // game without act gates). Re-enable that block to restore this test.
    test.skip('player cannot view clues from a locked act', () => {
      const clueData = {
        id: 'CLUE123',
        act: 'act_ii_mystery_emerges',
        skills: []
      };
      const state = createAccessState(clueData, {
        unlockedActs: [], // Act II not unlocked
        userSkills: []
      });

      expect(state.name).toBe('gated');
    });

    test('player can view clues after scanning a clue that unlocks the act', () => {
      // First, simulate scanning any one of the 4 Act II gate clues (AO79 here)
      const gateClue = {
        id: 'AO79',
        act: 'act_i_setting',
        story_gate_for: 'act_ii_mystery_emerges',
        skills: []
      };

      // After scanning gate clue, Act II should be unlocked
      const unlockedActs = ['act_ii_mystery_emerges'];

      // Now player can view Act II clues
      const actIIClue = {
        id: 'CLUE456',
        act: 'act_ii_mystery_emerges',
        skills: []
      };
      const state = createAccessState(actIIClue, {
        unlockedActs,
        userSkills: []
      });

      expect(state.name).toBe('unlocked');
    });

    test('player can always view Prologue clues', () => {
      const clueData = {
        id: 'PROLOGUE_CLUE',
        act: 'act_prologue',
        skills: []
      };
      const state = createAccessState(clueData, {
        unlockedActs: [], // No acts unlocked
        userSkills: []
      });

      expect(state.name).toBe('unlocked');
    });

    test('player can always view Act I clues', () => {
      const clueData = {
        id: 'ACTI_CLUE',
        act: 'act_i_setting',
        skills: []
      };
      const state = createAccessState(clueData, {
        unlockedActs: [], // No acts unlocked
        userSkills: []
      });

      expect(state.name).toBe('unlocked');
    });
  });

  describe('skill requirements', () => {
    test('player cannot view clue when lacking required expertise', () => {
      const clueData = {
        id: 'CLUE123',
        act: 'act_i_setting',
        skills: ['art_2'],
        type: 'Artifact (Object)'
      };
      const state = createAccessState(clueData, {
        unlockedActs: [],
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
        unlockedActs: [],
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
        unlockedActs: [],
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
        unlockedActs: [],
        userSkills: [] // No skills at all
      });

      expect(state.name).toBe('unlocked');
    });

    // Story-gate locking is currently DISABLED in clue-access.js. Re-enable
    // that block to restore this test.
    test.skip('player sees gate message even if they have the required skills', () => {
      const clueData = {
        id: 'CLUE123',
        act: 'act_ii_mystery_emerges',
        skills: ['art_2']
      };
      const state = createAccessState(clueData, {
        unlockedActs: [], // Act II not unlocked
        userSkills: ['art_2'] // Has skills, but gate blocks first
      });

      expect(state.name).toBe('gated');
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
