import type { AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import {
  applyLocationImport,
  createLocationGroup,
  previewLocationImport,
  uploadImage,
} from '@/api/generated/sdk.gen';
import axiosClient from '@/lib/axiosClient';

/**
 * These tests pin the shape of the request that leaves the axios client,
 * because the failure they guard against is silent: hand axios a FormData body
 * while a Content-Type of application/json is in effect and it re-serializes
 * the form to JSON, turning every File into `{}`. The API then rejects the
 * upload with a 422 naming the very fields the client believed it had sent, and
 * nothing is logged server-side because the request never reaches a handler.
 *
 * They assert on the config the *adapter* receives on purpose: that is the last
 * point before the wire, after interceptors and transformRequest have run, so a
 * regression anywhere along that chain is caught rather than just in one layer.
 */

const XLSX_TYPE =
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

const COLUMN_MAP = { address: 'Address', contact_name: 'Last Name' };

/** Five bytes, so an assertion on `size` can prove the bytes survived. */
function spreadsheet() {
  return new File([new Uint8Array([1, 2, 3, 4, 5])], 'roster.xlsx', {
    type: XLSX_TYPE,
  });
}

let sent: InternalAxiosRequestConfig | undefined;
const realAdapter = axiosClient.defaults.adapter;

function lastRequest(): InternalAxiosRequestConfig {
  if (!sent) throw new Error('No request reached the axios adapter');
  return sent;
}

function sentContentType(): string {
  return String(lastRequest().headers.get('Content-Type') ?? '');
}

function sentForm(): FormData {
  const { data } = lastRequest();
  if (!(data instanceof FormData)) {
    throw new Error(`Body was ${typeof data}, expected FormData`);
  }
  return data;
}

beforeEach(() => {
  sent = undefined;
  axiosClient.defaults.adapter = async (config) => {
    sent = config;
    return {
      data: {},
      status: 200,
      statusText: 'OK',
      headers: {},
      config,
    } as AxiosResponse;
  };
});

afterEach(() => {
  axiosClient.defaults.adapter = realAdapter;
});

const multipartOperations = [
  {
    name: 'previewLocationImport',
    send: () =>
      previewLocationImport({
        body: {
          file: spreadsheet(),
          column_map: JSON.stringify(COLUMN_MAP),
          delivery_type: 'Family',
        },
        throwOnError: true,
      }),
    scalars: {
      column_map: JSON.stringify(COLUMN_MAP),
      delivery_type: 'Family',
    },
  },
  {
    name: 'applyLocationImport',
    send: () =>
      applyLocationImport({
        body: {
          file: spreadsheet(),
          column_map: JSON.stringify(COLUMN_MAP),
          delivery_type: 'School',
        },
        throwOnError: true,
      }),
    scalars: {
      column_map: JSON.stringify(COLUMN_MAP),
      delivery_type: 'School',
    },
  },
  {
    name: 'uploadImage',
    send: () =>
      uploadImage({ body: { file: spreadsheet() }, throwOnError: true }),
    scalars: {},
  },
];

describe.each(multipartOperations)(
  '$name sends real multipart',
  ({ send, scalars }) => {
    it('keeps the body as FormData instead of a serialized string', async () => {
      await send();

      expect(lastRequest().data).toBeInstanceOf(FormData);
      // The regression turned the body into a JSON string; name that directly
      // so a failure reads as the actual bug rather than a type mismatch.
      expect(typeof lastRequest().data).not.toBe('string');
    });

    it('preserves the upload as a File with its bytes intact', async () => {
      await send();

      const file = sentForm().get('file');
      expect(file).toBeInstanceOf(File);
      expect((file as File).name).toBe('roster.xlsx');
      expect((file as File).size).toBe(5);
      expect((file as File).type).toBe(XLSX_TYPE);
    });

    it('leaves Content-Type unset so the browser can add the boundary', async () => {
      await send();

      expect(sentContentType()).not.toMatch(/application\/json/);
    });

    it('preserves the scalar form fields', async () => {
      await send();

      const form = sentForm();
      for (const [field, value] of Object.entries(scalars)) {
        expect(form.get(field)).toBe(value);
      }
    });
  }
);

describe('JSON operations are unaffected', () => {
  it('still send a JSON body labelled application/json', async () => {
    await createLocationGroup({
      body: { name: 'Tuesday A', location_ids: [] },
      throwOnError: true,
    });

    expect(sentContentType()).toMatch(/application\/json/);
    expect(typeof lastRequest().data).toBe('string');
    expect(JSON.parse(lastRequest().data as string)).toEqual({
      name: 'Tuesday A',
      location_ids: [],
    });
  });
});
