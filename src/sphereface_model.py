import torch
from .net_sphere import sphere20a


class SphereFaceEmbedder:
    def __init__(self, weights_path):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = sphere20a(feature=True).to(self.device).eval()
        state = torch.load(str(weights_path), map_location=self.device)
        self.model.load_state_dict(state)

    @torch.no_grad()
    def embed(self, face_tensor):
        if face_tensor.dim() == 3:
            face_tensor = face_tensor.unsqueeze(0)
        face_tensor = face_tensor.to(self.device)
        emb = self.model(face_tensor)[0]
        return emb.cpu()
