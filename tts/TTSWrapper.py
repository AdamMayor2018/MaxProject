# TTS模型类
from config.conf_loader import YamlConfigLoader
import numpy as np
import torch
from time import time as ttime
import librosa


class BaseTTSWrapper:
    def __init__(self, conf_loader: YamlConfigLoader):
        """
            TTS模型功能基类
        :param conf_loader:
        """
        self.conf_loader = conf_loader

    def load_model(self):
        raise NotImplementedError

    def tts_inference(self, text: str):
        raise NotImplementedError


class GPTSoVitsWrapper(BaseTTSWrapper):
    def __init__(self):
        super().__init__()
        self.is_half = self.conf_loader.attempt_load_param("")

    def load_model(self):
        pass

    def tts_inference(self, text: str):
        pass

    def get_tts_wav(self, ref_wav_path, prompt_text, prompt_language, text, text_language):
        t0 = ttime()
        prompt_text = prompt_text.strip("\n")
        prompt_language, text = prompt_language, text.strip("\n")
        zero_wav = np.zeros(int(hps.data.sampling_rate * 0.3), dtype=np.float16 if is_half == True else np.float32)
        with torch.no_grad():
            wav16k, sr = librosa.load(ref_wav_path, sr=16000)
            wav16k = torch.from_numpy(wav16k)
            zero_wav_torch = torch.from_numpy(zero_wav)
            if (is_half == True):
                wav16k = wav16k.half().to(device)
                zero_wav_torch = zero_wav_torch.half().to(device)
            else:
                wav16k = wav16k.to(device)
                zero_wav_torch = zero_wav_torch.to(device)
            wav16k = torch.cat([wav16k, zero_wav_torch])
            ssl_content = ssl_model.model(wav16k.unsqueeze(0))["last_hidden_state"].transpose(1, 2)  # .float()
            codes = vq_model.extract_latent(ssl_content)
            prompt_semantic = codes[0, 0]
        t1 = ttime()
        prompt_language = dict_language[prompt_language]
        text_language = dict_language[text_language]
        phones1, word2ph1, norm_text1 = clean_text(prompt_text, prompt_language)
        phones1 = cleaned_text_to_sequence(phones1)
        texts = text.split("\n")
        audio_opt = []

        for text in texts:
            phones2, word2ph2, norm_text2 = clean_text(text, text_language)
            phones2 = cleaned_text_to_sequence(phones2)
            if (prompt_language == "zh"):
                bert1 = get_bert_feature(norm_text1, word2ph1).to(device)
            else:
                bert1 = torch.zeros((1024, len(phones1)), dtype=torch.float16 if is_half == True else torch.float32).to(
                    device)
            if (text_language == "zh"):
                bert2 = get_bert_feature(norm_text2, word2ph2).to(device)
            else:
                bert2 = torch.zeros((1024, len(phones2))).to(bert1)
            bert = torch.cat([bert1, bert2], 1)

            all_phoneme_ids = torch.LongTensor(phones1 + phones2).to(device).unsqueeze(0)
            bert = bert.to(device).unsqueeze(0)
            all_phoneme_len = torch.tensor([all_phoneme_ids.shape[-1]]).to(device)
            prompt = prompt_semantic.unsqueeze(0).to(device)
            t2 = ttime()
            with torch.no_grad():
                # pred_semantic = t2s_model.model.infer(
                pred_semantic, idx = t2s_model.model.infer_panel(
                    all_phoneme_ids,
                    all_phoneme_len,
                    prompt,
                    bert,
                    # prompt_phone_len=ph_offset,
                    top_k=config['inference']['top_k'],
                    early_stop_num=hz * max_sec)
            t3 = ttime()
            # print(pred_semantic.shape,idx)
            pred_semantic = pred_semantic[:, -idx:].unsqueeze(0)  # .unsqueeze(0)#mq要多unsqueeze一次
            refer = get_spepc(hps, ref_wav_path)  # .to(device)
            if (is_half == True):
                refer = refer.half().to(device)
            else:
                refer = refer.to(device)
            # audio = vq_model.decode(pred_semantic, all_phoneme_ids, refer).detach().cpu().numpy()[0, 0]
            audio = \
                vq_model.decode(pred_semantic, torch.LongTensor(phones2).to(device).unsqueeze(0),
                                refer).detach().cpu().numpy()[
                    0, 0]  ###试试重建不带上prompt部分
            audio_opt.append(audio)
            audio_opt.append(zero_wav)
            t4 = ttime()
        print("%.3f\t%.3f\t%.3f\t%.3f" % (t1 - t0, t2 - t1, t3 - t2, t4 - t3))
        yield hps.data.sampling_rate, (np.concatenate(audio_opt, 0) * 32768).astype(np.int16)
