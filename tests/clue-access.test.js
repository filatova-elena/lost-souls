const { hasSkillAccess, parseSkill } = require('../src/lib/skills');
const { resolveClueState, buildSkillLockedMessage, getQuestClueIsKeyFor } = require('../src/js/clue-access');

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
  function createAccessState(clueData, { unlockedClues = [], unlockedActs = [], userSkills = [] }) {
    return resolveClueState(clueData, {
      unlockedClues,
      unlockedActs,
      userSkills,
      noAccessMessages: mockNoAccessMessages,
      hasSkillAccessFn: hasSkillAccess,
      parseSkillFn: parseSkill,
      randomFn: deterministicRandom
    });
  }

  describe('story gate progression', () => {
    test('player cannot view clues from a locked act', () => {
      const clueData = {
        id: 'CLUE123',
        act: 'act_ii_mystery_emerges',
        skills: []
      };
      const state = createAccessState(clueData, {
        unlockedClues: [],
        unlockedActs: [], // Act II not unlocked
        userSkills: []
      });

      expect(state.name).toBe('gated');
    });

    test('player can view clues after scanning a clue that unlocks the act', () => {
      // First, simulate scanning the gate clue (DL122) which unlocks Act II
      const gateClue = {
        id: 'DL122',
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
        unlockedClues: [],
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
        unlockedClues: [],
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
        unlockedClues: [],
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
        unlockedClues: [],
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
        unlockedClues: [],
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
        unlockedClues: [],
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
        unlockedClues: [],
        unlockedActs: [],
        userSkills: [] // No skills at all
      });

      expect(state.name).toBe('unlocked');
    });

    test('player sees gate message even if they have the required skills', () => {
      const clueData = {
        id: 'CLUE123',
        act: 'act_ii_mystery_emerges',
        skills: ['art_2']
      };
      const state = createAccessState(clueData, {
        unlockedClues: [],
        unlockedActs: [], // Act II not unlocked
        userSkills: ['art_2'] // Has skills, but gate blocks first
      });

      expect(state.name).toBe('gated');
    });
  });

  describe('octogram bypass', () => {
    test('player can view a skill-locked clue after solving its octogram puzzle', () => {
      const clueData = {
        id: 'CLUE123',
        act: 'act_i_setting',
        skills: ['art_2'],
        unlock_code: 'ABC123'
      };
      
      // Before solving octogram
      const beforeState = createAccessState(clueData, {
        unlockedClues: [],
        unlockedActs: [],
        userSkills: [] // No skills
      });
      expect(beforeState.name).toBe('skill-locked');

      // After solving octogram (clue is manually unlocked)
      const afterState = createAccessState(clueData, {
        unlockedClues: ['CLUE123'], // Manually unlocked via octogram
        unlockedActs: [],
        userSkills: [] // Still no skills, but bypass works
      });
      expect(afterState.name).toBe('unlocked');
    });
  });
});

describe('quest progress', () => {
  const mockProgressData = {
    mainQuestHashtag: 'main_quest',
    sideQuests: {
      alice: { hashtag: 'alice_side_quest' },
      bob: { hashtag: 'bob_side_quest' }
    }
  };

  test('finding a main quest key clue advances the main quest', () => {
    const clueData = {
      id: 'MAIN_KEY_CLUE',
      is_key: ['main_quest']
    };
    const result = getQuestClueIsKeyFor(clueData, {
      mainQuestHashtag: mockProgressData.mainQuestHashtag,
      sideQuests: mockProgressData.sideQuests,
      characterId: 'alice'
    });

    expect(result).toBe('main_quest');
  });

  test('finding a side quest key clue advances that character quest', () => {
    const clueData = {
      id: 'ALICE_KEY_CLUE',
      is_key: ['alice_side_quest']
    };
    const result = getQuestClueIsKeyFor(clueData, {
      mainQuestHashtag: mockProgressData.mainQuestHashtag,
      sideQuests: mockProgressData.sideQuests,
      characterId: 'alice'
    });

    expect(result).toBe('alice_side_quest');
  });

  test('finding another character side quest key clue does not advance any quest', () => {
    const clueData = {
      id: 'BOB_KEY_CLUE',
      is_key: ['bob_side_quest']
    };
    const result = getQuestClueIsKeyFor(clueData, {
      mainQuestHashtag: mockProgressData.mainQuestHashtag,
      sideQuests: mockProgressData.sideQuests,
      characterId: 'alice' // Different character
    });

    expect(result).toBeNull();
  });

  test('finding a non-key clue does not advance any quest', () => {
    const clueData = {
      id: 'REGULAR_CLUE',
      is_key: []
    };
    const result = getQuestClueIsKeyFor(clueData, {
      mainQuestHashtag: mockProgressData.mainQuestHashtag,
      sideQuests: mockProgressData.sideQuests,
      characterId: 'alice'
    });

    expect(result).toBeNull();
  });

  test('main quest progress takes priority over side quest', () => {
    const clueData = {
      id: 'DUAL_KEY_CLUE',
      is_key: ['main_quest', 'alice_side_quest'] // Key for both
    };
    const result = getQuestClueIsKeyFor(clueData, {
      mainQuestHashtag: mockProgressData.mainQuestHashtag,
      sideQuests: mockProgressData.sideQuests,
      characterId: 'alice'
    });

    expect(result).toBe('main_quest'); // Main quest takes priority
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
