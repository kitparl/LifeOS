import { FormControl } from '@angular/forms';
import { usernameFormatValidator } from './username.validator';

describe('usernameFormatValidator', () => {
  const validate = usernameFormatValidator();

  it('accepts valid usernames', () => {
    for (const value of ['john', 'john_smith', 'john.smith', 'dev123']) {
      expect(validate(new FormControl(value))).toBeNull();
    }
  });

  it('rejects invalid usernames', () => {
    expect(validate(new FormControl('123john'))).toEqual(
      jasmine.objectContaining({ usernameFormat: jasmine.any(String) }),
    );
    expect(validate(new FormControl('john__'))).toEqual(
      jasmine.objectContaining({ usernameFormat: jasmine.any(String) }),
    );
    expect(validate(new FormControl('admin'))).toEqual(
      jasmine.objectContaining({ usernameReserved: jasmine.any(String) }),
    );
  });
});
