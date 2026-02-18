const { hasSkillAccess, parseSkill } = require('../src/lib/skills');

// Mock browser environment
global.window = {
  getFromLocalStorage: jest.fn(),
  saveToLocalStorage: jest.fn(),
  getCharacterProfile: jest.fn(),
  hasSkillAccess: hasSkillAccess,
  parseSkill: parseSkill,
  convertSkills: jest.fn(skills => Array.isArray(skills) ? skills : [])
};

// Mock clue-page.js functions (we'll test the logic, not the full module)
function getUnlockedClues() {
  return window.getFromLocalStorage('unlocked', []);
}

function getScannedClues() {
  return window.getFromLocalStorage('scanned', { all: [] });
}

function generateNoAccessMessage(missingSkills, clueType, noAccessMessages) {
  if (!noAccessMessages || !noAccessMessages.skill_phrases || !noAccessMessages.wrappers) {
    return "You don't have the required skills to access this clue.";
  }
  
  const phrases = [];
  for (const skill of missingSkills) {
    const parsed = window.parseSkill(skill);
    if (!parsed) continue;
    
    const skillPhrases = noAccessMessages.skill_phrases[parsed.base];
    if (!skillPhrases) continue;
    
    let phraseArray;
    if (parsed.level > 0) {
      phraseArray = skillPhrases[`level_${parsed.level}`];
    } else {
      phraseArray = Array.isArray(skillPhrases) ? skillPhrases : null;
    }
    
    if (phraseArray && phraseArray.length > 0) {
      phrases.push(phraseArray[0]); // Use first item for deterministic tests
    }
  }
  
  if (phrases.length === 0) {
    phrases.push("the required expertise");
  }
  
  let wrappers = noAccessMessages.wrappers[clueType];
  if (!wrappers || wrappers.length === 0) {
    wrappers = noAccessMessages.wrappers._default || ["The meaning here escapes you. You'd need {requirements}."];
  }
  
  const wrapper = wrappers[0]; // Use first for deterministic tests
  const requirements = phrases.join(' or ');
  return wrapper.replace('{requirements}', requirements);
}

function resolveClueState(clueData, noAccessMessages) {
  if (getUnlockedClues().includes(clueData.id)) {
    return { name: 'unlocked' };
  }

  if (clueData.gate) {
    const scanned = getScannedClues();
    if (!(scanned.gates || []).includes(clueData.gate)) {
      return { name: 'gated' };
    }
  }

  const profile = window.getCharacterProfile();
  const userSkills = profile ? profile.skills : [];
  const hasAccess = window.hasSkillAccess(clueData.skills || [], userSkills);

  if (!hasAccess) {
    return {
      name: 'skill-locked',
      message: generateNoAccessMessage(clueData.skills || [], clueData.type, noAccessMessages),
      suggestedCharacters: clueData.accessChars
    };
  }

  return { name: 'unlocked' };
}

function getNewlyFoundQuest(clueData) {
  const keyHashtags = clueData.is_key || [];
  if (keyHashtags.length === 0) return null;

  const progressData = window.__progressData || {};
  const mainQuestHashtag = progressData.mainQuestHashtag || 'main_quest';
  if (keyHashtags.includes(mainQuestHashtag)) return mainQuestHashtag;

  const profile = window.getCharacterProfile();
  const sideQuests = progressData.sideQuests || {};
  const sideQuest = profile?.characterId ? sideQuests[profile.characterId] : null;
  if (sideQuest?.hashtag && keyHashtags.includes(sideQuest.hashtag)) return sideQuest.hashtag;

  return null;
}

// -- Tests --

describe('resolveClueState', () => {
  const mockNoAccessMessages = {
    skill_phrases: {
      art: {
        level_1: ['artistic knowledge'],
        level_2: ['expert artistic knowledge']
      },
      medical: {
        level_1: ['medical training'],
        level_2: ['expert medical training']
      }
    },
    wrappers: {
      'Artifact (Object)': ['You need {requirements} to understand this.'],
      '_default': ['The meaning here escapes you. You\'d need {requirements}.']
    }
  };

  beforeEach(() => {
    jest.clearAllMocks();
    window.getFromLocalStorage.mockReturnValue([]);
    window.getCharacterProfile.mockReturnValue(null);
  });

  test('returns unlocked if clue is in unlocked list', () => {
    window.getFromLocalStorage.mockImplementation((key) => {
      if (key === 'unlocked') return ['CLUE123'];
      return [];
    });

    const clueData = { id: 'CLUE123', skills: ['art_2'] };
    const state = resolveClueState(clueData, mockNoAccessMessages);

    expect(state.name).toBe('unlocked');
    expect(state.message).toBeUndefined();
  });

  test('returns gated if clue gate is not unlocked', () => {
    window.getFromLocalStorage.mockImplementation((key) => {
      if (key === 'unlocked') return [];
      if (key === 'scanned') return { all: [], gates: [] };
      return [];
    });

    const clueData = {
      id: 'CLUE123',
      gate: 'act_ii_mystery_emerges',
      skills: []
    };
    const state = resolveClueState(clueData, mockNoAccessMessages);

    expect(state.name).toBe('gated');
  });

  test('returns unlocked if clue gate is unlocked', () => {
    window.getFromLocalStorage.mockImplementation((key) => {
      if (key === 'unlocked') return [];
      if (key === 'scanned') return { all: [], gates: ['act_ii_mystery_emerges'] };
      return [];
    });

    const clueData = {
      id: 'CLUE123',
      gate: 'act_ii_mystery_emerges',
      skills: []
    };
    const state = resolveClueState(clueData, mockNoAccessMessages);

    expect(state.name).toBe('unlocked');
  });

  test('returns skill-locked if character lacks required skills', () => {
    window.getFromLocalStorage.mockImplementation((key) => {
      if (key === 'unlocked') return [];
      if (key === 'scanned') return { all: [] };
      return [];
    });
    window.getCharacterProfile.mockReturnValue({
      characterId: 'alice',
      skills: ['art_1'] // Only level 1, needs level 2
    });

    const clueData = {
      id: 'CLUE123',
      skills: ['art_2'],
      type: 'Artifact (Object)',
      accessChars: ['Bob']
    };
    const state = resolveClueState(clueData, mockNoAccessMessages);

    expect(state.name).toBe('skill-locked');
    expect(state.message).toContain('artistic');
    expect(state.suggestedCharacters).toEqual(['Bob']);
  });

  test('returns unlocked if character has required skills', () => {
    window.getFromLocalStorage.mockImplementation((key) => {
      if (key === 'unlocked') return [];
      if (key === 'scanned') return { all: [] };
      return [];
    });
    window.getCharacterProfile.mockReturnValue({
      characterId: 'alice',
      skills: ['art_2']
    });

    const clueData = {
      id: 'CLUE123',
      skills: ['art_2']
    };
    const state = resolveClueState(clueData, mockNoAccessMessages);

    expect(state.name).toBe('unlocked');
  });

  test('returns unlocked if clue has no skill requirements', () => {
    window.getFromLocalStorage.mockImplementation((key) => {
      if (key === 'unlocked') return [];
      if (key === 'scanned') return { all: [] };
      return [];
    });
    window.getCharacterProfile.mockReturnValue(null);

    const clueData = {
      id: 'CLUE123',
      skills: []
    };
    const state = resolveClueState(clueData, mockNoAccessMessages);

    expect(state.name).toBe('unlocked');
  });

  test('checks alchemical unlock before story gate', () => {
    window.getFromLocalStorage.mockImplementation((key) => {
      if (key === 'unlocked') return ['CLUE123'];
      if (key === 'scanned') return { all: [], gates: [] };
      return [];
    });

    const clueData = {
      id: 'CLUE123',
      gate: 'act_ii_mystery_emerges',
      skills: ['art_2']
    };
    const state = resolveClueState(clueData, mockNoAccessMessages);

    expect(state.name).toBe('unlocked');
  });

  test('checks story gate before skills', () => {
    window.getFromLocalStorage.mockImplementation((key) => {
      if (key === 'unlocked') return [];
      if (key === 'scanned') return { all: [], gates: [] };
      return [];
    });
    window.getCharacterProfile.mockReturnValue({
      characterId: 'alice',
      skills: ['art_2']
    });

    const clueData = {
      id: 'CLUE123',
      gate: 'act_ii_mystery_emerges',
      skills: ['art_2']
    };
    const state = resolveClueState(clueData, mockNoAccessMessages);

    expect(state.name).toBe('gated');
  });
});

describe('getNewlyFoundQuest', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    window.getCharacterProfile.mockReturnValue(null);
    window.__progressData = {
      mainQuestHashtag: 'main_quest',
      sideQuests: {
        alice: { hashtag: 'alice_side_quest' },
        bob: { hashtag: 'bob_side_quest' }
      }
    };
  });

  test('returns null if clue has no is_key', () => {
    const clueData = { id: 'CLUE123' };
    expect(getNewlyFoundQuest(clueData)).toBeNull();
  });

  test('returns null if is_key is empty array', () => {
    const clueData = { id: 'CLUE123', is_key: [] };
    expect(getNewlyFoundQuest(clueData)).toBeNull();
  });

  test('returns main_quest if clue is key for main quest', () => {
    const clueData = { id: 'CLUE123', is_key: ['main_quest'] };
    expect(getNewlyFoundQuest(clueData)).toBe('main_quest');
  });

  test('returns main_quest if clue is key for multiple quests including main', () => {
    const clueData = { id: 'CLUE123', is_key: ['main_quest', 'side_quest'] };
    expect(getNewlyFoundQuest(clueData)).toBe('main_quest');
  });

  test('returns side quest if clue is key for current character side quest', () => {
    window.getCharacterProfile.mockReturnValue({
      characterId: 'alice',
      skills: []
    });

    const clueData = { id: 'CLUE123', is_key: ['alice_side_quest'] };
    expect(getNewlyFoundQuest(clueData)).toBe('alice_side_quest');
  });

  test('returns null if clue is key for different character side quest', () => {
    window.getCharacterProfile.mockReturnValue({
      characterId: 'alice',
      skills: []
    });

    const clueData = { id: 'CLUE123', is_key: ['bob_side_quest'] };
    expect(getNewlyFoundQuest(clueData)).toBeNull();
  });

  test('returns null if no character profile', () => {
    window.getCharacterProfile.mockReturnValue(null);

    const clueData = { id: 'CLUE123', is_key: ['alice_side_quest'] };
    expect(getNewlyFoundQuest(clueData)).toBeNull();
  });
});
