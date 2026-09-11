#!/usr/bin/env python3
from pathlib import Path
from repair_grammar_english import apply_text_replacements

EXTRA = {
    'Cedille, apostrophe and trema':'Cedilla, Apostrophe and Diaeresis',
    'Case-sensitive':'Capitalization',
    'Satzzeichen':'Punctuation',
    'The debate':'Pronunciation',
    'The Pronunciation of the Vocals':'Pronunciation of Vowels',
    "The Consonants' Debate":'Pronunciation of Consonants',
    'The debate on:':'Pronunciation of',
    'Rule in the case of phrases':'Articles in Fixed Expressions',
    'The plural of the nouns':'Plural of Nouns',
    'Adjectives in the feminin form':'Feminine Form of Adjectives',
    'Adjectives with two masculine forms':'Adjectives with Two Masculine Forms',
    'The increase in adjectives':'Comparison of Adjectives',
    'The increase in adverbs':'Comparison of Adverbs',
    'The associated personnel pronouns':'Clitic Personal Pronouns',
    'The unconnected personnel pronouns':'Stressed Personal Pronouns',
    'The Posessive Pronouns':'Possessive Pronouns',
    'The verbs on ‑er':'Verbs Ending in ‑er',
    'The verbs on ‑ir':'Verbs Ending in ‑ir',
    'The verbs on ‑re':'Verbs Ending in ‑re',
    'The verbs on ‑oir':'Verbs Ending in ‑oir',
    'Reflexive Verben':'Reflexive Verbs',
    'Shortening of auxiliary sentences with the infinitive':'Reducing Subordinate Clauses with the Infinitive',
    'Complementing the verb (Valence)':'Verb Complements (Valency)',
    'direktes Objekt':'direct object',
    'Relative rates with':'Relative Clauses with',
    'Conversion of relative rates':'Alternatives to Relative Clauses',
    'Conditional rates with:':'Conditional Clauses with',
    'Other conditions':'Other Conditional Clauses',
    'Prepositions of the place':'Prepositions of Place',
    'Beiordnende Konjunktionen':'Coordinating Conjunctions',
    'Unterordnende Konjunktionen':'Subordinating Conjunctions',
    'Negation words':'Negative Expressions',
    'Negation with quantitative information':'Negation with Quantities',
    'The indirect speech':'Indirect Speech',
    'The sequence of times in indirect speech':'Sequence of Tenses in Indirect Speech',
    'Informelle Verneinung':'Informal Negation',
    'Informelle Fragen':'Informal Questions',
    'Fill words':'Discourse Fillers',
    'Zahlen':'Numbers',
    'Bruchzahlen':'Fractions',
    'Datumsangaben':'Dates',
    'Zeitangaben':'Time Expressions',
    'Familie':'Family',
    'Status and relations':'Status and Relationships',
    'Body and Health':'Body and Health',
    'House and apartment':'Home and Housing',
    'Kleidung':'Clothing',
    'Wetter':'Weather',
    'City and travel':'City and Travel',
    'Natur':'Nature',
    'Tiere':'Animals',
    'Berufe':'Professions',
    'Labour and the economy':'Work and the Economy',
    'Recht':'Law',
    'Farben':'Colors',
    'Materialien':'Materials',
    'Contradictions':'Opposites',
    'Zeit':'Time',
    'Bewegungsverben':'Motion Verbs',
    'Kommunikationsverben':'Communication Verbs',
    'Falsche Freunde':'False Friends',
    'Verbs of bringing and taking away':'Verbs of Bringing and Taking',
    'The forms of adverbs':'Formation of Adverbs',
    'The position of adverbs':'Position of Adverbs',
    'The position of the adjective':'Position of Adjectives',
    'The three types of questions':'Three Ways to Form Questions',
    'The question pronouns':'Interrogative Pronouns',
    'The verb':'The Verb',
    'Modal and auxiliary verbs':'Modal and Auxiliary Verbs',
    'Impersonal verbs':'Impersonal Verbs',
    'The Infinitive':'The Infinitive',
    'The indirect question':'The Indirect Question',
    'The Indirect Statement':'The Indirect Statement',
    'paraphrase of the':'Alternatives to the',
    'in a relative rate':'in a relative clause',
    'single and majority':'singular and plural',
    'single or majority':'singular or plural',
    'in single and majority':'in the singular and plural',
    'in the majority':'in the plural',
    'in the single':'in the singular',
    'female country names':'feminine country names',
    'male country names':'masculine country names',
    'male and female':'masculine and feminine',
    'female and male':'feminine and masculine',
    'male':'masculine',
    'female':'feminine',
}

# Do not apply the standalone male/female substitutions to vocabulary pages where the
# words can describe people or animals literally.
VOCAB_PREFIX = '99 Vokabeln/'

def main():
    pages=nodes=0
    for path in sorted(Path('grammar').rglob('*.html')):
        rel=str(path.relative_to('grammar'))
        local=dict(EXTRA)
        if rel.startswith(VOCAB_PREFIX):
            local.pop('male',None); local.pop('female',None)
        raw=path.read_text(encoding='utf-8')
        new,n=apply_text_replacements(raw,local)
        if n:
            path.write_text(new,encoding='utf-8'); pages+=1; nodes+=n
            print(f'{rel}: heading/terminology nodes={n}')
    print(f'GRAMMAR HEADING/TERMINOLOGY REPAIRS: pages={pages} nodes={nodes}')

if __name__=='__main__':
    main()
