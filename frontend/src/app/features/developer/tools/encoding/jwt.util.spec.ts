import { decodeJwt } from './jwt.util';

// header {"alg":"HS256","typ":"JWT"}, payload {"sub":"1234567890","name":"John Doe","iat":1516239022}
const SAMPLE_JWT =
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c';

describe('jwt.util', () => {
  it('decodes a valid JWT', () => {
    const result = decodeJwt(SAMPLE_JWT);
    expect(result.header).toEqual({ alg: 'HS256', typ: 'JWT' });
    expect((result.payload as { name: string }).name).toBe('John Doe');
    expect(result.issuedAt).toBeTruthy();
  });

  it('throws a clear error for malformed tokens', () => {
    expect(() => decodeJwt('not.a.jwt.token')).toThrowError(/3 dot-separated parts/);
    expect(() => decodeJwt('onlyonepart')).toThrowError();
  });
});
