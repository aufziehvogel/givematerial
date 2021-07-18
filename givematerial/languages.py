import givematerial.extractors


SUPPORTED_LANGUAGES = {
    'es': 'Spanish',
    'hr': 'Croatian',
    'jp': 'Japanese',
}


def get_lemmatizer(language: str, **kwargs) -> givematerial.extractors.LearnableExtractor:
    if language == 'hr':
        if not 'freqs_file' in kwargs:
            raise ValueError('Croatian lemmatizer requires a frequencies file')

        return givematerial.extractors.CroatianLemmatizer(kwargs['freqs_file'])
    elif language == 'es':
        return givematerial.extractors.SpacyLemmatizer('es_core_news_lg')
    elif language == 'jp':
        return givematerial.extractors.JapaneseKanjiExtractor()
    else:
        raise NotImplementedError(
            f'Extractor for language "{language}" does not exist')
