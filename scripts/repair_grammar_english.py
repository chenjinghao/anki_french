#!/usr/bin/env python3
"""Deterministic reviewed English repairs for grammar prose.

Edits text nodes only. French (`.fr`), IPA (`.ipa`), code, attributes, IDs and legacy
compatibility classes are never touched.  Replacements are deliberately explicit so
quality fixes are auditable and regression-testable.
"""
from __future__ import annotations

import re
from pathlib import Path

TAG_SPLIT=re.compile(r'(<[^>]+>)',re.S)
OPEN=re.compile(r'<\s*([A-Za-z0-9:_-]+)\b([^>]*)>')
CLOSE=re.compile(r'</\s*([A-Za-z0-9:_-]+)\s*>')
CLASS=re.compile(r'\bclass\s*=\s*(["\'])(.*?)\1',re.I|re.S)
VOID={'br','hr','img','meta','link','input','source','wbr'}

GLOBAL = {
    'The specific Article':'The Definite Article',
    'The specific article':'The definite article',
    'The specific Articles':'The definite articles',
    'the specific Articles':'the definite articles',
    'The particular article':'The definite article',
    'the particular article':'the definite article',
    'certain Articles':'definite articles',
    'certain Article':'definite article',
    'indeterminate Articles':'indefinite articles',
    'indeterminate Article':'indefinite article',
    'Indeterminate Article':'Indefinite Article',
    'The Indeterminate Pronoun':'The Indefinite Pronoun',
    'The Indeterminate Demonstrative Pronouns':'The Indefinite Demonstrative Pronouns',
    'The indeterminate demonstrative pronouns':'The indefinite demonstrative pronouns',
    'divisional article':'partitive article',
    'division article':'partitive article',
    'The divisional article':'The Partitive Article',
    'The division article':'The partitive article',
    'stummem h':'silent h',
    'stummen h-Lauten':'aspirated h sounds',
    'stummen h':'silent h',
    'stummem H':'silent h',
    '(Bindung)':'(linking)',
    'the Friends':'the friends',
    'This process is called elimination.':'This process is called elision.',
    'prepositioned':'preceded',
    'The Order Numbers':'Ordinal Numbers',
    'the order numbers':'ordinal numbers',
    'the order number':'the ordinal number',
    'order number':'ordinal number',
    'basic number':'cardinal number',
    'basic figures':'cardinal numbers',
    'counter (the upper number)':'numerator (the upper number)',
    'apostrophed':'elided',
    'The Possessive Companions':'Possessive Determiners',
    'The Possessed Companions':'The possessive determiners',
    'Possessive companions':'Possessive determiners',
    'possessive companion':'possessive determiner',
    'The Indefinite Companions':'Indefinite Determiners',
    'Indefinite companions':'Indefinite determiners',
    'indefinite companion':'indefinite determiner',
    'Demonstrative companions':'Demonstrative determiners',
    'demonstrative companion':'demonstrative determiner',
    'The demonstrators':'Demonstrative Determiners',
    'demonstrators':'demonstrative determiners',
    'The sex of the nouns':'The Gender of Nouns',
    'Sex in living beings':'Gender of People and Animals',
    'The sex of things and things':'Gender of Inanimate Nouns',
    'Sex-related punctuation':'Gender and Noun Endings',
    'Differences in meaning due to sex change':'Meaning Changes with Grammatical Gender',
    'male and female nouns':'masculine and feminine nouns',
    'male and female forms':'masculine and feminine forms',
    'male form':'masculine form',
    'female form':'feminine form',
    'male singular':'masculine singular',
    'female singular':'feminine singular',
    'male plural':'masculine plural',
    'female plural':'feminine plural',
    'male noun':'masculine noun',
    'female noun':'feminine noun',
    'male country names':'masculine country names',
    'female country names':'feminine country names',
    'in number and sex':'in number and gender',
    'in sex and number':'in gender and number',
    'in the sex':'in gender',
    'each sex':'each gender',
    'different sexes':'different genders',
    'the different sexes':'the different genders',
    'its article and sex':'its article and gender',
    'number and sex':'number and gender',
    'sex and number':'gender and number',
    'word type':'part of speech',
    'sentence members':'sentence elements',
    'The Verb Derivative Rules':'Deriving Verb Forms',
    'verb trunk':'verb stem',
    'the trunk':'the stem',
    'The trunk':'The stem',
    'the tribe':'the stem',
    'The tribe':'The stem',
    'plural presence':'plural present tense',
    'person plural presence':'person plural present tense',
    'The French has':'French has',
    'memorabilia':'mnemonic',
    'by the annexing of':'by adding',
    'by attaching':'by adding',
    'Hanged.':'added.',
    'Hanged':'added',
    'conjunctiv':'subjunctive',
    'Conjunctiv':'Subjunctive',
    'Zusammengesetzte Substantive':'Compound Nouns',
    'Adjektive im Plural':'Plural Adjectives',
    'Adjektive':'adjectives',
    'Substantive':'nouns',
    'Pronomen':'pronouns',
    'Infinitiv':'infinitive',
    'Imperativen':'imperatives',
    'Imperativformen':'imperative forms',
    'Hilfsverb':'auxiliary verb',
    'Verneinungen':'negations',
    'Verneinung':'negation',
    'Ausnahmen:':'Exceptions:',
    'Ausnahme:':'Exception:',
    'Endungen':'endings',
    'Endung':'ending',
    'gebildet.':'formed.',
    'gebildet:':'formed:',
    'ausgesprochen.':'pronounced.',
    'meistens ausgesprochen.':'usually pronounced.',
    'verwendet:':'used:',
    'Sonderfall:':'Special case:',
    'Zahlwort':'numeral',
    'Mengenangabe':'quantity expression',
    'Nominalgruppen':'noun phrases',
    'Sachsubstantiven':'inanimate nouns',
    'Personensubstantiv':'noun referring to a person',
    'Sachbegriffen':'inanimate concepts',
}

PATH = {
'03 Artikel/1 Der bestimmte Artikel.html': {
    'In French, the definite article is used in some cases where it does not appear in German:':'French uses the definite article in several contexts where English normally does not:',
    'The definite article is used in French for most country names.':'French uses the definite article with most country names.',
    'In the case of feminine country names, the article is not used if it is preceded':'With feminine country names, no article is used after',
    'stehen:':':',
    'is based on the':'agrees with the',
    'This process is called elision.':'This process is called elision.',
},
'03 Artikel/2 Der unbestimmte Artikel.html': {
    'In German there is no indefinite article in the plural. In French, for this there is no indefinite article in the plural.':'French uses des as the plural indefinite article.',
    'It corresponds to the German plural without article or also "some".':'In English it is often translated with no article or with “some”.',
    'After a denial':'After negation',
    'After a':'After',
    'before an adjective in the plural':'before a plural adjective',
    'If the noun is preceded by an adjective in the plural, the article':'If a plural noun is preceded by an adjective,',
},
'03 Artikel/3 Der Teilungsartikel.html': {
    ') is used to express an indeterminate amount of something that is not countable (e.g. water, courage) or its exact number is not relevant (e.g. fries). In German, there is often no article for this.':') expresses an unspecified quantity of something uncountable (e.g. water, courage) or a non-specific quantity of countable items (e.g. fries). In English it is often translated with “some” or no article.',
    'It is derived from the preposition':'It is formed from the preposition',
    'When an adjective is in the plural, it becomes the noun.':'When a plural noun is preceded by an adjective,',
    'erhalten, z.B.':'is retained, e.g.',
    '(junge Leute)':'(young people)',
    'Meine Schwester spielt Geige.':'My sister plays the violin.',
    '(genug)':'(enough)',
    '(viel)':'(a lot of)',
    '(wenig)':'(little / few)',
    '(Too much)':'(too much / too many)',
    '(one group)':'(a group)',
    '(One kilo)':'(one kilo)',
    '(a package)':'(a packet)',
    '(one bottle)':'(one bottle)',
},
'04 Substantive/01 Das Geschlecht der Substantive.html': {
    'In French there are only masculine and feminine nouns. The German neutrum does not exist. The sex can differ from the German (e.g.':'French nouns are either masculine or feminine. Grammatical gender must be learned with the noun because it cannot always be predicted from meaning (e.g.',
    'Since gender is often only recognized by the article, nouns should always be taught with their article and gender.':'Because gender is often indicated by the article, learn nouns together with their article.',
    'For persons or animals, there is usually a separate form for each gender. For the formation of the feminine form, there are the following rules and exceptions:':'For many people and animals, masculine and feminine forms are distinguished. Common formation patterns and exceptions include:',
},
'04 Substantive/02 Das Geschlecht bei bestimmten Wortendungen.html': {
    'Some nouns exist in both masculine and feminine form. These words conceal a difference of meaning behind the different genders, e.g.:':'Some nouns occur in both masculine and feminine forms with different meanings, e.g.:',
    '♀ Ausnahmen':'♀ Exceptions',
    '♂ Ausnahmen':'♂ Exceptions',
},
'05 Adjektive/1 Die Stellung des Adjektivs.html': {
    'the noun. The acronym serves as a mnemonic':'the noun. The mnemonic',
},
'05 Adjektive/2 Adjektive im Plural.html': {
    'In principle, the plural form is defined by adding a':'As a rule, the plural is formed by adding',
    'The feminine form is usually formed by adding to the masculine singular form a':'The feminine form is usually formed by adding',
    'An adjective in the masculine form already ends':'If a masculine adjective already ends',
},
'06 Adverbien/1 Die Formen von Adverbien.html': {
    '1. Principle: formation of the feminine form':'1. Basic rule: use the feminine adjective form',
    'The adverb is formed by the ending -ment to the feminine form of the adjective added.':'Form the adverb by adding -ment to the feminine form of the adjective.',
},
'07 Pronomen/03 Die direkten Objektpronomen.html': {
    '; COD) replace a direct object (accumulator object).':'; COD) replace a direct object.',
    'The direct object pronouns match the replaced object in number and gender, e.g.:':'A preceding direct object can trigger past-participle agreement in compound tenses, e.g.:',
    'Die direkten Objektpronomen stehen vor dem konjugierten Verb. Bei':'Direct object pronouns come before the conjugated verb. With',
    'umschließt die negation das Objektpronomen und das konjugierte Verb.':'the negative expression surrounds the object pronoun and the conjugated verb.',
    'Bei Verben mit':'With verbs followed by an',
    'steht das direkte Objektpronomen vor dem infinitive.':'the direct object pronoun comes before the infinitive.',
    'Bei':'With',
    'wird das Objektpronomen mit Bindestrich an den bejahten Imperativ angehängt.':'the object pronoun is attached to an affirmative imperative with a hyphen.',
},
'07 Pronomen/04 Die indirekten Objektpronomen.html': {
    '; COI) replace a dative object.':'; COI) replace an indirect object, usually introduced by à.',
    'make it easier for one in French, since the direct and indirect object pronouns have the same form.':'have the same forms as the corresponding direct object pronouns.',
    'The indirect object pronouns correspond in number to the Dative object. These Dative objects are almost always persons and animals.':'Indirect object pronouns agree in number with the person or animate referent they replace.',
    'For masculine and feminine dative objects there is only one indirect object pronoun.':'The third-person singular form lui is used for both masculine and feminine referents.',
    'Im Französischen kann man aus':'In French,',
    'nicht erkennen, ob es sich um eine männliche oder weibliche Person handelt!':'does not show whether the person referred to is masculine or feminine.',
    'Die indirekten Objektpronomen stehen vor dem konjugierten Verb. Wird der Satz verneint, so umschließt die negation das Objektpronomen und das konjugierte Verb.':'Indirect object pronouns come before the conjugated verb. In a negative sentence, the negative expression surrounds the object pronoun and the conjugated verb.',
    'Steht der Satz im':'In the',
    'oder im':'or',
    ', dann steht das Objektpronomen vor dem konjugierten':', the object pronoun comes before the conjugated',
    'Bei Verben, die einen':'With verbs followed by an',
    'bei sich haben, steht das indirekte Objektpronomen vor dem infinitive.':', the indirect object pronoun comes before the infinitive.',
},
'07 Pronomen/06 Das Adverbialpronomen en.html': {
    'The Pronoun':'The pronoun',
    'replaces additions with:':'replaces complements introduced by de, including:',
    'den':'the',
    '+ Substantiv:':'+ noun:',
    'Wenn':'When',
    'eine quantity expression, ein numeral oder':'replaces a quantity expression, numeral, or',
    '+ noun vertritt, wird die quantity expression, das numeral oder der unbestimmte Artikel im nachfolgenden Satz wiederholt.':'+ noun, the quantity, numeral, or indefinite article is repeated in the following clause.',
    'vertritt auch andere Ergänzungen mit':'also replaces other complements introduced by',
    '. In diesen Fällen wird':'. In these cases,',
    'oft mit':'is often translated as',
    'davon':'of it / some',
    'darüber':'about it',
    'von dort':'from there',
    'oder':'or',
    'dorther':'from there',
    'übersetzt.':'in English.',
    'vertritt Ergänzungen mit':'replaces complements with',
    '+ inanimate nounn, z.B. nach den Verben':'+ inanimate nouns, e.g. after the verbs',
    'usw.:':'etc.:',
    'Wenn auf die Präposition':'When the preposition',
    'ein noun referring to a person folgt, übernehmen die betonten Personalpronomen die Vertretung, z.B.:':'is followed by a noun referring to a person, use a stressed personal pronoun instead, e.g.:',
    'Die Stellung von en':'Position of en',
    'steht vor dem konjugierten Verb. Bei einer':'comes before the conjugated verb. With a',
    'umschließt die negation':'the negative expression surrounds',
    'und das konjugierte Verb. Im':'and the conjugated verb. In the',
    'steht':'comes',
    'vor dem konjugierten':'before the conjugated',
    'Bei Verben mit einem':'With verbs followed by an',
    'vor dem infinitive.':'before the infinitive.',
    'wird':'is',
    'an den bejahten Imperativ mit einem Bindestrich angehängt.':'attached to an affirmative imperative with a hyphen.',
    'Verben auf':'verbs ending in',
    'wird an den Imperativ Singular des Verbs ein':'add',
    'angehängt.':'to the singular imperative.',
},
'07 Pronomen/07 Das Adverbialpronomen y.html': {
    'The Pronoun':'The pronoun',
    'ersetzt:':'replaces:',
    'Location information which is provided by:':'place expressions introduced by',
    'Prepositions':'prepositions',
    'how':'such as',
    'to be launched:':'and similar prepositions:',
    'Ergänzungen mit':'complements with',
    '+ inanimate conceptsen:':'+ inanimate nouns or concepts:',
    'Das Pronomen':'The pronoun',
    'wird nie für':'is never used for',
    'verwendet, auch nicht bei Ortsangaben!':'even with place expressions.',
    'Die Position von y im Satz':'Position of y in the sentence',
    'steht vor dem konjugierten Verb. Bei':'comes before the conjugated verb. With',
    'umschließt die negation':'the negative expression surrounds',
    'und das konjugierte Verb. Im':'and the conjugated verb. In the',
    'vor dem':'before the',
    'Bei Verben mit':'With verbs followed by an',
    'direkt vor dem infinitive.':'directly before the infinitive.',
    'Bei bejahten':'With affirmative',
    'mit einem Bindestrich angehängt. Achtung: Bei Verben auf':'is attached with a hyphen. Note: with verbs ending in',
    'und dem unregelmäßigen Verb':'and the irregular verb',
    'wird im Singular ein':'the singular imperative takes an',
    'angefügt.':'before y.',
},
'07 Pronomen/09 Die Demonstrativbegleiter.html': {
    'Demonstrative determiners have an indicative function: They determine a noun closer. In German there are two demonstrative determiners:':'Demonstrative determiners point out or identify a noun more precisely. French uses:',
    'The French has only one who adapts in gender and number to the noun accompanied.':'French demonstrative determiners agree in gender and number with the noun they modify.',
},
'07 Pronomen/11 Die Possessivbegleiter.html': {
    'Unlike in German, the French possessor does not depend on the gender of the owner, but on the number and gender of the possessed thing!':'French possessive determiners agree with the possessed noun in gender and number, not with the gender of the possessor.',
    'In front of a feminine noun, with vowel or':'Before a feminine noun beginning with a vowel or',
},
'07 Pronomen/13 Die Indefinitbegleiter.html': {
    'Indefinite determiners stand with a noun. They denote an indefinite quantity or an indefinite identity.':'Indefinite determiners accompany a noun and express an unspecified quantity or identity.',
    'They are always plural and adapt to the noun in gender.':'They are always plural and agree with the noun in gender.',
    'adapts in gender and number to the noun.':'agrees in gender and number with the noun.',
    'is immutable in gender and number.':'is invariable in gender and number.',
},
'07 Pronomen/14 Die Indefinitpronomen.html': {
    'Indefinite pronouns represent a':'Indefinite pronouns replace a',
    'They denote an indefinite amount or an indefinite identity.':'They express an unspecified quantity or identity.',
    'Als pronouns der negation werden sie immer mit':'As negative pronouns, they are always used with',
    'gebraucht, stehen im Singular und passen sich im Geschlecht an.':'; they are singular and agree in gender.',
    'Wird verwendet, um eine Alternative oder einen Unterschied auszudrücken:':'Used to express an alternative or a contrast:',
    'Die festen Wendungen':'The fixed expressions',
    'sind unveränderlich.':'are invariable.',
    'Wird verwendet, um eine unbestimmte Menge oder Auswahl auszudrücken:':'Used to express an unspecified quantity or selection:',
    'Als Indefinitpronomen steht':'As an indefinite pronoun,',
    'immer im Plural und passt sich im Geschlecht an.':'is always plural and agrees in gender.',
    'Bezieht sich auf jede einzelne Person oder Sache einer Gruppe:':'Refers to each individual person or thing in a group:',
    'steht immer im Singular und passt sich im Geschlecht an. Es bezeichnet jede einzelne Person oder Sache aus einer Gruppe.':'is always singular and agrees in gender. It refers to each individual member of a group.',
    'Wird verwendet, um auf etwas bereits Erwähntes hinzuweisen:':'Used to refer back to something already mentioned:',
    'Drücken Beliebigkeit aus:':'Express an unrestricted choice:',
    'Zu dieser Gruppe gehören auch':'This group also includes',
    'Wird verwendet, um aus einer Gruppe beliebig auszuwählen:':'Used to choose any member of a group:',
    'passt sich in Geschlecht und Zahl an das Bezugswort an.':'agrees in gender and number with its antecedent.',
    'Wird als Subjekt in unpersönlichen Sätzen verwendet und bezieht sich auf Personen im Allgemeinen:':'Used as a subject to refer to people in general:',
    'kann verschiedene Bedeutungen haben: allgemeine Personen (man), jemand, oder auch "wir" in der Umgangssprache. Nach':'can mean people in general, someone, or informal “we”. After',
    'kann in der gehobenen Sprache':'formal style may use',
    'statt':'instead of',
    'stehen, außer wenn das folgende Wort mit l- beginnt.':', except before a word beginning with l-.',
    'Wird verwendet, um eine unbestimmte Menge im Plural auszudrücken:':'Used to express an unspecified plural quantity:',
    'ist als Indefinitpronomen unveränderlich und steht immer im Plural.':'is invariable as an indefinite pronoun and is always plural.',
    'Bezeichnen unbestimmte Sachen oder Begriffe:':'Refer to unspecified things or concepts:',
    'stehen immer im Singular und sind unveränderlich.':'are always singular and invariable.',
    'wird in verneinten Sätzen verwendet. Bei zusammengesetzten Zeitformen steht':'is used in negative sentences. In compound tenses it comes',
    'zwischen':'between the',
    'und':'and',
    'Bezeichnet eine unbestimmte Anzahl von Personen oder Sachen:':'Refers to an unspecified number of people or things:',
    'steht immer im Plural und passt sich im Geschlecht an das vertretene noun an.':'is always plural and agrees in gender with the noun it replaces.',
    'Bezeichnen eine unbestimmte bzw. keine Person:':'Refer to an unspecified person or to nobody:',
    'wird in verneinten Sätzen verwendet.':'is used in negative sentences.',
    'Bezeichnet eine beliebige Person unter bestimmten Bedingungen:':'Refers to any person meeting the stated condition:',
    'ist unveränderlich und bezieht sich auf Personen.':'is invariable and refers to people.',
    'Verweist auf vorher erwähnte Lebewesen oder Dinge. Die zweite Variante mit dem Personalpronomen':'Refers back to previously mentioned people, animals, or things. The variant with the personal pronoun',
    'wird häufiger verwendet.':'is more common.',
    'steht auch als neutrale Singularform. Bei den zusammengesetzten Zeiten steht':'also has an invariable neutral singular use. In compound tenses it comes',
},
'09 Verben/06 Die Ableitungsregeln der Verben.html': {
    'The stem of the 1st person plural':'The stem of the first-person plural',
    'The stem of the 3rd person plural present tense (form with':'The stem of the third-person plural present tense (the form with',
    'Infinitiv + ending':'infinitive + ending',
},
'10 Zeitformen und Modi/01 Présent.html': {
    '(Presence) is a simple form of time of the indicative. It describes, similar to in German, present events and actions that take place at the time of speaking, as well as habits and general facts.':'is a simple indicative tense used for actions happening now, habitual actions, and general facts.',
},
'10 Zeitformen und Modi/12 Subjonctif.html': {
    'It should not be confused with the German subjunctive, e.g. in indirect speech.':'The French subjunctive is a mood used in specific subordinate-clause contexts; it is not simply equivalent to the English subjunctive.',
},
'18 Verneinung/04 Verneinung ohne ne.html': {
    'Diese Konstruktion wird häufig in kurzen Mitteilungen und Schildern verwendet.':'This construction is common in short notices and signs.',
},
'20 Indirekte Rede/1 Die indirekte Rede.html': {
    'The indirect speech is used to reproduce words, thoughts or desires without quoting them literally. In French, unlike in German, there is no subjunctive, but rather a subjunctive.':'Indirect speech reports words, thoughts, or wishes without quoting them directly. French normally uses the indicative in reported statements rather than a special reported-speech mood.',
},
'22 Zahlen und Zeitangaben/2 Ordnungszahlen.html': {
    'The ordinal numbers are formed by the ending':'Ordinal numbers are normally formed by adding',
    'to the respective cardinal number.':'to the corresponding cardinal number.',
    'The article before the ordinal numbers is never elided, even before vowel or':'The article before an ordinal number is not elided, even before a vowel or',
    'Rulers of a name use the ordinal number. For all following days or rulers the cardinal number is used.':'For dates, premier is used for the first day of a month; other dates use cardinal numbers. Regnal numbers follow their conventional forms.',
    '+ cardinal number or':'+ cardinal number or',
},
'22 Zahlen und Zeitangaben/3 Bruchzahlen.html': {
    'Most fractions are derived from the ordinal numbers. The denominator (the lower number) corresponds to the':'Most fraction names are based on ordinal numbers. The denominator (the lower number) corresponds to the',
    'If the numerator (the upper number) is greater than 1, the ordinal number in the denominator is given a plural‑':'If the numerator is greater than 1, the denominator normally takes a plural -s.',
},
}


def apply_text_replacements(raw: str, local: dict[str,str]) -> tuple[str,int]:
    parts=TAG_SPLIT.split(raw)
    stack=[]
    changes=0
    mapping=dict(GLOBAL); mapping.update(local)
    ordered=sorted(mapping.items(), key=lambda kv: len(kv[0]), reverse=True)
    for i,part in enumerate(parts):
        if not part: continue
        if part.startswith('<'):
            cm=CLOSE.fullmatch(part.strip())
            if cm:
                if stack: stack.pop()
                continue
            om=OPEN.match(part)
            if om and not part.rstrip().endswith('/>'):
                tag=om.group(1).lower(); attrs=om.group(2)
                cls=CLASS.search(attrs); classes=set(cls.group(2).split()) if cls else set()
                protected=(stack[-1][1] if stack else False) or bool(classes & {'fr','ipa'}) or tag in {'code','script','style'}
                if tag not in VOID: stack.append((tag,protected))
            continue
        if stack and stack[-1][1]: continue
        value=part
        for old,new in ordered:
            if old in value:
                value=value.replace(old,new)
        if value!=part:
            changes += 1; parts[i]=value
    return ''.join(parts),changes


def main() -> int:
    total=pages=0
    for path in sorted(Path('grammar').rglob('*.html')):
        rel=str(path.relative_to('grammar'))
        raw=path.read_text(encoding='utf-8')
        new,n=apply_text_replacements(raw,PATH.get(rel,{}))
        if n:
            path.write_text(new,encoding='utf-8'); total+=n; pages+=1
            print(f'{rel}: repaired text nodes={n}')
    print(f'GRAMMAR REVIEWED PROSE REPAIRS: pages={pages} text_nodes={total}')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
