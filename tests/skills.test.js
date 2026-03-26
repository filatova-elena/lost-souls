const { hasSkillAccess, convertSkills, charactersWithAccess } = require('../src/lib/skills');

function characterCanAccess(character, clueSkills) {
  const skills = convertSkills(character.skills);
  return hasSkillAccess(clueSkills, skills);
}

// -- Tests --

describe('clue access', () => {
  const alice = { id: 'alice', skills: ['art_2'] };
  const bob = { id: 'bob', skills: ['medical_2'] };
  const charlie = { id: 'charlie', skills: { expert: ['art'], basic: ['history'] } };

  test('character with matching skill can access clue', () => {
    expect(characterCanAccess(alice, ['art_2', 'history_2'])).toBe(true);
  });

  test('character without matching skills cannot access clue', () => {
    expect(characterCanAccess(bob, ['art_2', 'history_2'])).toBe(false);
  });

  test('only one matching skill is needed (OR logic)', () => {
    // Charlie has art_2 (via nested format) but only history_1, still gets access
    expect(characterCanAccess(charlie, ['art_2', 'history_2'])).toBe(true);
  });

  test('clues with no skill requirements are accessible to everyone', () => {
    expect(characterCanAccess(alice, [])).toBe(true);
    expect(characterCanAccess(bob, [])).toBe(true);
  });
});

describe('skill levels', () => {
  const expert = { id: 'expert', skills: ['medical_2'] };
  const basic = { id: 'basic', skills: ['medical_1'] };

  test('expert level grants access to basic clues', () => {
    expect(characterCanAccess(expert, ['medical_1'])).toBe(true);
  });

  test('basic level does NOT grant access to expert clues', () => {
    expect(characterCanAccess(basic, ['medical_2'])).toBe(false);
  });

  test('exact level match grants access', () => {
    expect(characterCanAccess(expert, ['medical_2'])).toBe(true);
    expect(characterCanAccess(basic, ['medical_1'])).toBe(true);
  });
});

describe('personal skills', () => {
  const alice = { id: 'alice', skills: ['personal_family_a'] };
  const bob = { id: 'bob', skills: ['personal_family_b'] };

  test('characters can access clues about their personal connections', () => {
    expect(characterCanAccess(alice, ['personal_family_a'])).toBe(true);
    expect(characterCanAccess(bob, ['personal_family_b'])).toBe(true);
  });

  test('characters cannot access other characters\' personal clues', () => {
    expect(characterCanAccess(alice, ['personal_family_b'])).toBe(false);
    expect(characterCanAccess(bob, ['personal_family_a'])).toBe(false);
  });
});

describe('which characters can help with a clue', () => {
  const characters = [
    { id: 'alice', title: 'Alice', skills: ['art_2'], is_player: true },
    { id: 'bob', title: 'Bob', skills: ['medical_2'], is_player: true },
    { id: 'narrator', title: 'Narrator', skills: ['art_2'], is_player: false },
  ];

  test('finds player characters with matching skills', () => {
    expect(charactersWithAccess(['art_2'], characters)).toEqual(['Alice']);
  });

  test('excludes non-player characters even if they have matching skills', () => {
    expect(charactersWithAccess(['art_2'], characters)).not.toContain('Narrator');
  });

  test('returns empty when no players match', () => {
    expect(charactersWithAccess(['history_2'], characters)).toEqual([]);
  });
});

describe('mixed skill requirements', () => {
  const alice = { id: 'alice', skills: ['personal_family_a', 'art_2'] };
  const bob = { id: 'bob', skills: ['art_2'] };
  const charlie = { id: 'charlie', skills: ['medical_2'] };

  test('clue accessible via personal OR leveled skill', () => {
    // A clue requiring personal_family_a OR art_1
    const mixedClue = ['personal_family_a', 'art_1'];
    expect(characterCanAccess(alice, mixedClue)).toBe(true);  // has both
    expect(characterCanAccess(bob, mixedClue)).toBe(true);   // has art_2
    expect(characterCanAccess(charlie, mixedClue)).toBe(false); // has neither
  });
});

describe('nested skill format (backward compatibility)', () => {
  const nested = { id: 'nested', skills: { expert: ['art'], basic: ['history'] } };
  const flat = { id: 'flat', skills: ['art_2', 'history_1'] };

  test('nested format works the same as flat format', () => {
    expect(characterCanAccess(nested, ['art_2'])).toBe(true);
    expect(characterCanAccess(nested, ['history_1'])).toBe(true);
    expect(characterCanAccess(nested, ['history_2'])).toBe(false);
  });

  test('nested and flat formats produce equivalent results', () => {
    expect(characterCanAccess(nested, ['art_2'])).toBe(characterCanAccess(flat, ['art_2']));
    expect(characterCanAccess(nested, ['history_1'])).toBe(characterCanAccess(flat, ['history_1']));
    expect(characterCanAccess(nested, ['history_2'])).toBe(characterCanAccess(flat, ['history_2']));
  });
});
