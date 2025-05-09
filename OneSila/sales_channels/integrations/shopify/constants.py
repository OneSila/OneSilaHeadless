DEFAULT_METAFIELD_NAMESPACE = 'onesila'

ACTIVE_STATUS = 'ACTIVE'
NON_ACTIVE_STATUS = 'DRAFT'
ALLOW_BACKORDER_CONTINUE = 'CONTINUE'
ALLOW_BACKORDER_DENY = 'DENY'


MEDIA_FRAGMENT = '''
fragment fieldsForMediaTypes on Media {
  alt
  mediaContentType
  preview {
    image {
      id
      altText
      url
    }
  }
  status
  ... on Video {
    id
    sources {
      format
      height
      mimeType
      url
      width
    }
    originalSource {
      format
      height
      mimeType
      url
      width
    }
  }
  ... on ExternalVideo {
    id
    host
    embeddedUrl
  }
  ... on Model3d {
    sources {
      format
      mimeType
      url
    }
    originalSource {
      format
      mimeType
      url
    }
  }
  ... on MediaImage {
    id
    image {
      altText
      url
    }
  }
}
'''

def get_metafields(max):
    return f'''
    metafields(first: {max}) {{
      edges {{
        node {{
          id
          namespace
          key
          value
          type
          ownerType
        }}
      }}
    }}
    '''
