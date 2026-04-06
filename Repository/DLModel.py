import torch
import torch.nn as nn
import torch.nn.functional as F

# From DLTRCodev2GA.py
img_size = 480

class CombinedNet(nn.Module):
    def __init__(self):
        super(CombinedNet, self).__init__()
        # Convolutional branch
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.pool  = nn.MaxPool2d(2, 2)

        # Compute flattened dimension after 3 pools
        h, w = img_size, int(img_size * 0.625)
        # Correct calculation for output size after pooling
        h_out = h // 2 // 2 // 2
        w_out = w // 2 // 2 // 2
        flat_dim = 128 * h_out * w_out

        self.fc_img = nn.Linear(flat_dim, 128)

        # Numerical branch
        self.fc_num1 = nn.Linear(3, 64)
        self.fc_num2 = nn.Linear(64, 128)

        # Combined head
        self.fc1    = nn.Linear(128 + 128, 256)
        self.fc2    = nn.Linear(256, 128)
        self.fc3    = nn.Linear(128, 64)
        self.fc_out = nn.Linear(64, 12)

    def forward(self, img, num):
        # Image branch
        x = F.relu(self.conv1(img))
        x = self.pool(x)
        x = F.relu(self.conv2(x))
        x = self.pool(x)
        x = F.relu(self.conv3(x))
        x = self.pool(x)
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc_img(x))

        # Numerical branch
        y = F.relu(self.fc_num1(num))
        y = F.relu(self.fc_num2(y))

        # Combined
        combined = torch.cat([x, y], dim=1)
        z = F.relu(self.fc1(combined))
        z = F.relu(self.fc2(z))
        z = F.relu(self.fc3(z))
        out = self.fc_out(z)
        return out 